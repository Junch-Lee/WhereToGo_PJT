import json
import logging

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ai.agent import run_agent
from apps.accounts.models import Topic
from apps.curriculum.models import (
    Curriculum,
    CurriculumCategory,
    CurriculumCourse,
    CurriculumStep,
    CurriculumStepCourse,
    CurriculumStepProgress,
    CurriculumStepResource,
    LearningProgress,
    LearningResource,
    LearningSchedule,
)
from apps.curriculum.services.curriculum_create_service import create_curriculum_for_user
from apps.curriculum.services.agent_response_service import normalize_agent_response
from apps.curriculum.services.curriculum_save_service import save_ai_generated_curriculum
from apps.curriculum.services.curriculum_learning_service import (
    CurriculumLearningError,
    complete_current_step,
    pause_curriculum_learning,
    start_curriculum_learning,
)
from apps.curriculum.services.topic_catalog_service import build_topic_catalog

from .serializers import (
    CurriculumCreateSerializer,
    CurriculumDetailSerializer,
    CurriculumGenerateSerializer,
    CurriculumLearningResponseSerializer,
    CurriculumListSerializer,
    CurriculumStartRequestSerializer,
    TopicSerializer,
)
from apps.curriculum.models import (
    Curriculum,
    CurriculumCategory,
    CurriculumCourse,
    CurriculumStep,
    CurriculumStepCourse,
    CurriculumStepProgress,
    CurriculumStepResource,
    LearningProgress,
    LearningResource,
    LearningSchedule,
)
from apps.curriculum.services.curriculum_create_service import create_curriculum_for_user

from .serializers import (
    CurriculumCreateSerializer,
    CurriculumDetailSerializer,
    CurriculumGenerateSerializer,
    CurriculumListSerializer,
    TopicSerializer,
)


logger = logging.getLogger(__name__)


def _apply_request_profile_to_generated_result(normalized_result, validated_data):
    """사용자가 선택한 생성 조건을 미리보기 user_profile에 다시 반영한다.

    AI가 내부 응답에서 ``target_weeks`` 같은 사용자 조건을 빠뜨리거나 기본값으로 되돌려도,
    결과 페이지의 총 학습기간/예상 완료일은 실제 프론트 선택값을 기준으로 보여야 한다.
    """
    user_profile = dict(normalized_result.get("user_profile") or {})
    for key in (
        "goal",
        "purpose",
        "difficulty_level",
        "target_weeks",
        "weekly_available_hours",
        "preferred_learning_style",
    ):
        if key in validated_data:
            user_profile[key] = validated_data[key]

    normalized_result["user_profile"] = user_profile
    return normalized_result


def _attach_preview_references(normalized_result):
    """결과 페이지 미리보기용 추천 자료/강의 이름을 identifier에 붙인다.

    AI는 저장 안정성을 위해 resource/course identifier만 반환한다. 하지만 결과 페이지에는
    사용자가 읽을 수 있는 이름이 필요하므로, 저장 전 미리보기 응답에만 DB 표시 정보를 덧붙인다.
    """
    steps = normalized_result.get("steps") or []
    resource_ids = {
        external_id
        for step in steps
        for external_id in step.get("resource_external_ids", [])
    }
    course_row_numbers = {
        row_number
        for step in steps
        for row_number in step.get("course_source_row_numbers", [])
    }

    resources_by_key = {
        resource.lookup_key: resource
        for resource in LearningResource.objects.filter(lookup_key__in=resource_ids)
    }
    courses_by_row_number = {
        course.source_row_number: course
        for course in CurriculumCourse.objects.filter(source_row_number__in=course_row_numbers)
    }

    for step in steps:
        step["preview_resources"] = [
            {
                "external_id": external_id,
                "title": resources_by_key[external_id].title,
                "resource_type": resources_by_key[external_id].resource_type,
                "provider_name": resources_by_key[external_id].provider_name,
            }
            for external_id in step.get("resource_external_ids", [])
            if external_id in resources_by_key
        ]
        step["preview_courses"] = [
            {
                "source_row_number": row_number,
                "course_name": courses_by_row_number[row_number].course_name,
                "university_name": courses_by_row_number[row_number].university_name,
            }
            for row_number in step.get("course_source_row_numbers", [])
            if row_number in courses_by_row_number
        ]

    return normalized_result


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def topics(request):
    """
    GET /api/topics/

    커리큘럼 생성 화면에서 선택하거나 참고할 수 있는 활성 토픽 목록을 반환한다.
    인증된 사용자만 호출할 수 있으며, 토픽을 생성하거나 수정하지 않는 조회 전용 API다.
    """
    queryset = Topic.objects.filter(is_active=True).order_by("id")
    serializer = TopicSerializer(queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def curriculums(request):
    """
    GET /api/curriculums/
    POST /api/curriculums/

    GET:
        현재 로그인한 사용자가 소유한 커리큘럼 목록만 최신순으로 반환한다.

    POST:
        요청 body를 CurriculumCreateSerializer로 검증한 뒤, 커리큘럼 생성 흐름을
        create_curriculum_for_user service에 위임한다.

    설계 경계:
        view는 인증, 입력 검증, service 호출, 응답 직렬화만 담당한다. 목표 분석,
        사용자 프로필 fallback, 단계 저장 같은 비즈니스 로직은 service 계층에 둔다.
    """
    if request.method == "GET":
        queryset = Curriculum.objects.filter(user=request.user).order_by(
            "-created_at",
            "-id",
        )
        serializer = CurriculumListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = CurriculumCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    curriculum = create_curriculum_for_user(
        request.user,
        serializer.validated_data,
    )
    response_serializer = CurriculumDetailSerializer(curriculum)
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_curriculum(request):
    """AI Agent 기반 커리큘럼 생성 API.

    처리 흐름:
        1. 요청 body를 ``CurriculumGenerateSerializer``로 검증한다.
        2. 검증된 데이터를 AI 입력 계약인 ``raw_input``으로 변환한다.
        3. 백엔드가 Topic catalog를 만들어 AI에 전달한다.
        4. ``run_agent(raw_input, catalog)``로 AI graph를 실행한다.
        5. AI 내부 결과를 backend guide 기준 status/schema로 정규화한다.
        6. ``success``일 때만 저장 service를 호출하고, 나머지 status는 저장하지 않는다.

    View가 직접 저장 로직을 구현하지 않는 이유:
        View는 HTTP orchestration만 담당해야 한다. identifier -> FK 조회, transaction,
        누락 FK 방어는 저장 service의 책임이고, AI 응답 계약 변환은 agent response
        service의 책임이다. 이렇게 나눠야 API 계층이 얇고 테스트하기 쉬워진다.

    success 외 status를 저장하지 않는 이유:
        out_of_scope, needs_clarification, no_results는 사용자에게 안내하거나 추가 입력을
        받아야 하는 상태다. 이 상태를 Curriculum row로 저장하면 빈 계획이나 실패 결과가
        사용자의 커리큘럼 목록에 남을 수 있다.

    AI 호출 실패를 별도로 처리하는 이유:
        AI graph는 외부 LLM, vector search 같은 런타임 의존성을 가질 수 있다. 예외의
        상세 내용을 사용자에게 그대로 노출하지 않고, 서버 로그에 제한적으로 남긴 뒤
        gateway 오류로 응답한다.
    """
    serializer = CurriculumGenerateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # request.data를 그대로 AI에 넘기지 않고, serializer가 검증한 값만 AI 입력 schema로 변환한다.
    raw_input = serializer.to_raw_input()

    try:
        # AI는 ORM에 접근하지 않으므로 백엔드가 active Topic catalog를 만들어 전달한다.
        catalog = build_topic_catalog()
        # run_agent는 AI graph 실행 지점이다. 개인정보가 섞일 수 있는 raw_input 전체는 로그에 남기지 않는다.
        agent_result = run_agent(raw_input, catalog)
        # AI graph가 실제로 반환한 원본 결과를 그대로 확인하기 위한 개발용 로그다.
        # 아래 normalized preview 로그와 비교하면 정규화 과정에서 어떤 값이 바뀌는지 볼 수 있다.
        logger.warning(
            "[AI_AGENT_RAW_RESULT] %s",
            json.dumps(agent_result, ensure_ascii=False, default=str),
        )
    except Exception:
        # TODO: 운영 단계에서는 AI timeout, vector search 실패 등 더 구체적인 예외로 좁히는 것이 좋다.
        logger.exception("AI curriculum generation failed.")
        return Response(
            {
                "status": "error",
                "message": "AI 커리큘럼 생성 중 오류가 발생했습니다.",
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )

    try:
        # AI 내부 generation_status를 백엔드 API 계약 status로 변환한다.
        normalized_result = normalize_agent_response(agent_result)
        if normalized_result.get("status") == "success":
            normalized_result = _apply_request_profile_to_generated_result(
                normalized_result,
                serializer.validated_data,
            )
            normalized_result = _attach_preview_references(normalized_result)
    except ValueError:
        logger.exception("AI curriculum generation returned an unsupported status.")
        return Response(
            {
                "status": "error",
                "message": "AI 응답 상태를 해석할 수 없습니다.",
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )

    result_status = normalized_result["status"]
    if result_status == "success":
        # 생성 직후에는 DB에 저장하지 않고 결과 페이지에서 보여줄 미리보기 데이터만 반환한다.
        # FK 조회와 transaction 처리는 사용자가 저장 버튼을 누른 뒤 별도 저장 API에서 담당한다.
        # 프론트의 CurriculumResult 페이지가 받는 값과 같은 payload를 확인할 수 있도록 로그에 남긴다.
        logger.warning(
            "[AI_GENERATED_CURRICULUM_PREVIEW] %s",
            json.dumps(normalized_result, ensure_ascii=False, default=str),
        )
        return Response(
            {
                "status": "success",
                "message": "커리큘럼 생성이 완료되었습니다.",
                "generated_curriculum": normalized_result,
            },
            status=status.HTTP_200_OK,
        )

    # 아래 status들은 저장 대상이 아니라 사용자 안내/추가 질문용 응답이다.
    if result_status == "needs_clarification":
        return Response(
            {
                "status": "needs_clarification",
                "clarification_question": normalized_result.get("clarification_question", ""),
            },
            status=status.HTTP_200_OK,
        )

    if result_status == "out_of_scope":
        return Response(
            {
                "status": "out_of_scope",
                "message": normalized_result.get("message", ""),
            },
            status=status.HTTP_200_OK,
        )

    if result_status == "no_results":
        return Response(
            {
                "status": "no_results",
                "message": normalized_result.get("message", ""),
            },
            status=status.HTTP_200_OK,
        )

    logger.error("Unexpected normalized AI status: %s", result_status)
    return Response(
        {
            "status": "error",
            "message": "AI 응답 상태를 해석할 수 없습니다.",
        },
        status=status.HTTP_502_BAD_GATEWAY,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_generated_curriculum(request):
    """AI 생성 결과를 사용자가 확정했을 때만 DB에 저장한다.

    ``generate_curriculum``은 결과 페이지에서 렌더링할 미리보기 데이터만 반환한다.
    이 view는 같은 normalized AI 결과를 받아 기존 저장 서비스에 위임하므로,
    생성 완료 페이지의 버튼을 누르기 전까지는 Curriculum/Step row가 생기지 않는다.
    """
    generated_curriculum = request.data.get("generated_curriculum")

    if not isinstance(generated_curriculum, dict):
        return Response(
            {
                "status": "error",
                "message": "저장할 커리큘럼 생성 결과가 필요합니다.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if generated_curriculum.get("status") != "success":
        return Response(
            {
                "status": "error",
                "message": "성공적으로 생성된 커리큘럼만 저장할 수 있습니다.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        curriculum = save_ai_generated_curriculum(request.user, generated_curriculum)
    except ValueError as exc:
        logger.warning("Invalid generated curriculum save request: %s", exc)
        return Response(
            {
                "status": "error",
                "message": "저장할 수 없는 커리큘럼 생성 결과입니다.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "status": "success",
            "curriculum_id": curriculum.id,
            "message": "커리큘럼이 저장되었습니다.",
            "curriculum": CurriculumDetailSerializer(curriculum).data,
        },
        status=status.HTTP_201_CREATED,
    )


def _get_user_curriculum_or_404(user, curriculum_id):
    """다른 사용자의 curriculum id 접근 시 존재 여부가 드러나지 않게 404로 처리한다."""
    return get_object_or_404(Curriculum.objects.filter(user=user), id=curriculum_id)


def _learning_error_response(exc):
    return Response(
        {
            "status": "error",
            "message": str(exc),
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def start_curriculum(request, curriculum_id):
    """
    POST /api/curriculums/{curriculum_id}/start/

    현재 로그인한 사용자의 커리큘럼에서 다음 미완료 step 하나만 학습 시작 처리한다.
    """
    serializer = CurriculumStartRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    curriculum = _get_user_curriculum_or_404(request.user, curriculum_id)
    try:
        result = start_curriculum_learning(
            curriculum,
            request.user,
            scheduled_date=serializer.validated_data.get("scheduled_date"),
        )
    except CurriculumLearningError as exc:
        return _learning_error_response(exc)

    response_serializer = CurriculumLearningResponseSerializer(result)
    return Response(response_serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def pause_curriculum(request, curriculum_id):
    """
    POST /api/curriculums/{curriculum_id}/pause/

    가장 최근 진행 중인 step과 연결된 진행 기록만 일시정지한다.
    """
    curriculum = _get_user_curriculum_or_404(request.user, curriculum_id)
    try:
        result = pause_curriculum_learning(curriculum, request.user)
    except CurriculumLearningError as exc:
        return _learning_error_response(exc)

    response_serializer = CurriculumLearningResponseSerializer(result)
    return Response(response_serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def complete_curriculum(request, curriculum_id):
    """
    POST /api/curriculums/{curriculum_id}/complete/

    MVP에서는 전체 커리큘럼 강제 완료가 아니라 현재 진행 중인 step 완료로 처리한다.
    """
    curriculum = _get_user_curriculum_or_404(request.user, curriculum_id)
    try:
        result = complete_current_step(curriculum, request.user)
    except CurriculumLearningError as exc:
        return _learning_error_response(exc)

    response_serializer = CurriculumLearningResponseSerializer(result)
    return Response(response_serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def curriculum_detail(request, curriculum_id):
    """
    GET /api/curriculums/{curriculum_id}/

    커리큘럼 상세 페이지에서 사용하는 중첩 조회 API다. 커리큘럼 기본 정보, 카테고리,
    전체 단계, 단계별 추천 자료/강의, 현재 단계의 진행 상태/일정/학습 기록을 함께 반환한다.

    권한 정책:
        현재 로그인한 사용자의 커리큘럼만 조회한다. 다른 사용자의 curriculum_id로 접근해도
        존재 여부가 노출되지 않도록 404를 반환한다.

    조회 전용 원칙:
        이 API는 learning_schedules, learning_progresses, curriculum_step_progresses를
        새로 만들거나 수정하지 않는다. 학습 시작, 일시정지, 재개, 완료 처리는 별도 API의
        책임으로 남겨둔다.
    """
    step_progress_queryset = (
        CurriculumStepProgress.objects.select_related("curriculum_step")
        .prefetch_related(
            Prefetch(
                "schedules",
                queryset=LearningSchedule.objects.order_by(
                    "scheduled_date",
                    "sequence_no",
                    "id",
                ),
            ),
            Prefetch(
                "learning_progresses",
                queryset=LearningProgress.objects.order_by("-studied_at", "-id"),
            ),
        )
        .order_by("id")
    )

    step_queryset = (
        CurriculumStep.objects.select_related("target_topic")
        .prefetch_related(
            Prefetch(
                "step_resources",
                queryset=CurriculumStepResource.objects.select_related(
                    "learning_resource",
                ).order_by("sort_order", "id"),
            ),
            Prefetch(
                "step_courses",
                queryset=CurriculumStepCourse.objects.select_related(
                    "curriculum_course",
                ).order_by("sort_order", "id"),
            ),
            Prefetch("progress_records", queryset=step_progress_queryset),
        )
        .order_by("step_order", "id")
    )

    curriculum = get_object_or_404(
        # user 조건을 queryset에 포함해 타인의 커리큘럼 존재 여부가 드러나지 않게 한다.
        Curriculum.objects.filter(user=request.user)
        .select_related("current_step")
        .prefetch_related(
            Prefetch(
                "curriculum_categories",
                queryset=CurriculumCategory.objects.select_related("category").order_by(
                    "-is_primary",
                    "id",
                ),
            ),
            Prefetch("steps", queryset=step_queryset),
            Prefetch("step_progresses", queryset=step_progress_queryset),
        ),
        id=curriculum_id,
    )

    serializer = CurriculumDetailSerializer(curriculum)
    return Response(serializer.data, status=status.HTTP_200_OK)
