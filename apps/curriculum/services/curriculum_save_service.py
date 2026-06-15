"""
생성된 커리큘럼 계획을 DB row로 저장하는 service.

Curriculum, CurriculumStep, 카테고리/자료/강의 연결 row를 하나의 transaction 안에서 저장한다.
학습 일정과 실제 진행 기록은 커리큘럼 생성 시점에 만들지 않고, 학습 시작/단계 시작 API의
책임으로 남겨둔다.
"""

from django.db import transaction
import logging

from apps.accounts.models import Topic
from apps.curriculum.models import (
    Curriculum,
    CurriculumCategory,
    CurriculumCourse,
    CurriculumStep,
    CurriculumStepCourse,
    CurriculumStepResource,
    LearningResource,
)


logger = logging.getLogger(__name__)

TOPIC_SLUG_FALLBACKS = {
    "computer-science": "computer-science-basics",
}


@transaction.atomic
def save_generated_curriculum(user, context, generated_plan):
    """
    생성된 커리큘럼 plan을 DB에 원자적으로 저장한다.

    입력값:
        user: 커리큘럼을 소유할 인증 사용자.
        context: build_curriculum_context가 만든 정규화된 생성 context.
        generated_plan: generate_curriculum_plan이 반환한 고정 schema의 plan.

    반환값:
        저장된 Curriculum 인스턴스. 관련 step은 curriculum.steps로 조회할 수 있다.

    현재 구현:
        curricula 부모 row를 먼저 만들고, 선택적으로 curriculum_categories를
        연결한 뒤, curriculum_steps와 선택적 resource/course 연결 row를 저장한다.

    transaction.atomic을 쓰는 이유:
        Curriculum만 저장되고 Step 저장에서 실패하는 불완전한 상태를 막기 위해서다.
        어느 child row 저장에서든 오류가 발생하면 전체 생성 작업이 rollback된다.

    향후 확장 지점:
        AI/RAG/Agent 결과가 더 많은 메타데이터를 포함하게 되면, generated_plan을
        DB row로 매핑하는 책임은 이 함수 안에 유지한다. 그래야 view는 얇게
        유지되고 저장 실패 처리도 한 곳에서 관리된다.
    """
    curriculum = Curriculum.objects.create(
        user=user,
        title=generated_plan["title"],
        goal=context["goal"],
        status=Curriculum.Status.DRAFT,
        target_weeks=context["target_weeks"],
        weekly_available_hours=context["weekly_available_hours"],
        difficulty_level=generated_plan["difficulty_level"],
        preferred_learning_style=context["preferred_learning_style"],
        recommendation_reason=generated_plan["recommendation_reason"],
    )

    for index, category in enumerate(context["categories"]):
        CurriculumCategory.objects.create(
            curriculum=curriculum,
            category=category,
            is_primary=index == 0,
        )

    for step_data in generated_plan["steps"]:
        step = CurriculumStep.objects.create(
            curriculum=curriculum,
            step_order=step_data["step_order"],
            title=step_data["title"],
            description=step_data["description"],
            target_topic=step_data["target_topic"],
            difficulty_level=step_data["difficulty_level"],
            estimated_hours=step_data["estimated_hours"],
            prerequisite_note=step_data["prerequisite_note"],
        )

        for sort_order, resource in enumerate(step_data["resources"], start=1):
            CurriculumStepResource.objects.create(
                curriculum_step=step,
                learning_resource=resource,
                reason="현재 키워드 기반 검색에서 목표와 관련된 자료로 선택되었습니다.",
                sort_order=sort_order,
            )

        for sort_order, course in enumerate(step_data["courses"], start=1):
            CurriculumStepCourse.objects.create(
                curriculum_step=step,
                curriculum_course=course,
                reason="현재 키워드 기반 검색에서 목표와 관련된 강의로 선택되었습니다.",
                sort_order=sort_order,
            )

    return curriculum


@transaction.atomic
def save_ai_generated_curriculum(user, ai_result: dict):
    """
    AI Agent가 반환한 identifier 기반 커리큘럼 결과를 DB row로 저장한다.

    이 함수가 필요한 이유:
        AI Agent는 Django ORM에 접근하지 않고 DB 객체도 반환하지 않는다. 대신
        ``target_topic_slug``, ``course_source_row_numbers``, ``resource_external_ids``
        같은 식별자만 반환한다. 백엔드는 이 식별자를 실제 모델 FK로 조회하고,
        Curriculum/Step/연결 row를 저장할 책임이 있다.

    저장 순서:
        1. Curriculum 생성
        2. CurriculumStep 생성
        3. CurriculumStepCourse 연결
        4. CurriculumStepResource 연결

    transaction을 사용하는 이유:
        부모 Curriculum과 여러 Step/연결 row는 하나의 생성 작업이다. 중간에 예상하지
        못한 DB 오류가 나면 일부 row만 남는 불완전한 상태를 막기 위해 전체 저장을
        하나의 transaction으로 묶는다.

    FK 누락 시 전체 저장을 실패시키지 않는 이유:
        AI 검색/생성 결과의 일부 identifier가 현재 DB와 맞지 않을 수 있다. Topic은
        모델상 null을 허용하므로 None으로 저장하고, Course/Resource 연결은 skip한다.
        이렇게 해야 유효한 나머지 커리큘럼 구조는 저장하면서 누락 데이터는 로그로
        추적할 수 있다.

    Args:
        user: 생성된 Curriculum의 소유자.
        ai_result: agent_response_service를 통과한 normalized AI 결과 dict.

    Returns:
        생성된 Curriculum 인스턴스.

    Raises:
        ValueError: ``ai_result["status"]``가 ``success``가 아닌 경우. out_of_scope,
            needs_clarification, no_results는 저장 대상이 아니므로 View/service 상위
            계층에서 응답 분기로 처리해야 한다.
    """
    # 저장 service는 success 결과만 다룬다. 실패/분기 status를 저장하면 사용자에게
    # 보여줄 안내 메시지가 빈 Curriculum row로 남을 수 있으므로 명확히 차단한다.
    if ai_result.get("status") != "success":
        raise ValueError("Only successful AI results can be saved.")

    logger.info("AI curriculum save started.")

    user_profile = ai_result.get("user_profile") or {}
    curriculum = Curriculum.objects.create(
        user=user,
        title=_clean_text(ai_result.get("title")) or _clean_text(user_profile.get("goal")),
        goal=_clean_text(user_profile.get("goal")),
        status=Curriculum.Status.DRAFT,
        target_weeks=_as_int(user_profile.get("target_weeks"), default=8),
        weekly_available_hours=_as_int(user_profile.get("weekly_hours"), default=7),
        difficulty_level=_clean_text(user_profile.get("difficulty_level")) or "beginner",
        preferred_learning_style=_clean_text(user_profile.get("preferred_learning_style")) or "balanced",
        recommendation_reason=_clean_text(ai_result.get("recommendation_reason")),
    )
    logger.info("AI curriculum parent created: curriculum_id=%s", curriculum.id)

    for step_data in ai_result.get("steps") or []:
        step = CurriculumStep.objects.create(
            curriculum=curriculum,
            step_order=_as_int(step_data.get("order"), default=0),
            title=_clean_text(step_data.get("title")),
            description=_clean_text(step_data.get("description")),
            target_topic=_find_topic(step_data.get("target_topic_slug")),
            difficulty_level=_clean_text(step_data.get("difficulty_level")) or curriculum.difficulty_level,
            estimated_hours=_as_int(step_data.get("estimated_hours"), default=0),
            prerequisite_note=_clean_text(step_data.get("prerequisite_note")),
        )

        for sort_order, course in enumerate(
            _find_courses(step_data.get("course_source_row_numbers")),
            start=1,
        ):
            CurriculumStepCourse.objects.create(
                curriculum_step=step,
                curriculum_course=course,
                reason="AI가 추천한 강의 식별자를 백엔드에서 CurriculumCourse로 매칭했습니다.",
                sort_order=sort_order,
            )

        for sort_order, resource in enumerate(
            _find_resources(step_data.get("resource_external_ids")),
            start=1,
        ):
            CurriculumStepResource.objects.create(
                curriculum_step=step,
                learning_resource=resource,
                reason="AI가 추천한 자료 식별자를 백엔드에서 LearningResource로 매칭했습니다.",
                sort_order=sort_order,
            )

    logger.info("AI curriculum save completed: curriculum_id=%s", curriculum.id)
    return curriculum


def _find_topic(slug: object):
    normalized_slug = _normalize_topic_slug(slug)
    if not normalized_slug:
        return None

    topic = Topic.objects.filter(slug=normalized_slug).first()
    if not topic:
        # target_topic은 null 허용 필드다. 없는 slug 때문에 전체 저장을 실패시키지 않고
        # step은 저장하되, 누락 slug는 후속 데이터 정합성 점검을 위해 로그로 남긴다.
        logger.warning("AI target topic slug not found: slug=%s", normalized_slug)
    return topic


def _normalize_topic_slug(slug: object) -> str:
    cleaned = _clean_text(slug)
    if not cleaned:
        return ""

    # AI validator는 아직 computer-science를 fallback으로 반환할 수 있지만, 현재
    # fixture/DB의 실제 slug는 computer-science-basics다. AI 영역을 수정하지 않는
    # PR 범위이므로 저장 계층에서만 호환 mapping으로 방어한다.
    return TOPIC_SLUG_FALLBACKS.get(cleaned, cleaned)


def _find_courses(source_row_numbers) -> list[CurriculumCourse]:
    courses = []
    for source_row_number in _unique_values(source_row_numbers):
        course = CurriculumCourse.objects.filter(source_row_number=source_row_number).first()
        if not course:
            # 일부 추천 강의가 DB에 없어도 Curriculum/Step 저장은 유효하다. 연결 row만
            # skip하고 어떤 identifier가 빠졌는지 로그로 남긴다.
            logger.warning(
                "AI course source_row_number not found: source_row_number=%s",
                source_row_number,
            )
            continue
        courses.append(course)
    return courses


def _find_resources(external_ids) -> list[LearningResource]:
    resources = []
    for external_id in _unique_values(external_ids):
        resource = LearningResource.objects.filter(lookup_key=external_id).first()
        if not resource:
            # LearningResource.lookup_key == AI external_id 계약을 따르되, 누락 자료는
            # 전체 저장 실패가 아니라 해당 연결만 제외한다.
            logger.warning("AI resource external_id not found: external_id=%s", external_id)
            continue
        resources.append(resource)
    return resources


def _unique_values(values) -> list:
    # 같은 step 안의 중복 identifier는 unique_together 제약과 중복 연결 생성을 피하기
    # 위해 입력 순서를 유지한 채 한 번만 처리한다.
    seen = set()
    result = []
    for value in values or []:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _clean_text(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _as_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
