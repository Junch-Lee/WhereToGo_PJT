"""
생성된 커리큘럼 계획을 DB row로 저장하는 service.

Curriculum, CurriculumStep, 카테고리/자료/강의 연결 row를 하나의 transaction 안에서 저장한다.
학습 일정과 실제 진행 기록은 커리큘럼 생성 시점에 만들지 않고, 학습 시작/단계 시작 API의
책임으로 남겨둔다.
"""

from django.db import transaction

from apps.curriculum.models import (
    Curriculum,
    CurriculumCategory,
    CurriculumStep,
    CurriculumStepCourse,
    CurriculumStepResource,
)


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
