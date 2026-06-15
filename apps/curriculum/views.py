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
    CurriculumStep,
    CurriculumStepCourse,
    CurriculumStepProgress,
    CurriculumStepResource,
    LearningProgress,
    LearningSchedule,
)
from apps.curriculum.services.curriculum_create_service import create_curriculum_for_user
from apps.curriculum.services.agent_response_service import normalize_agent_response
from apps.curriculum.services.curriculum_save_service import save_ai_generated_curriculum
from apps.curriculum.services.topic_catalog_service import build_topic_catalog

from .serializers import (
    CurriculumCreateSerializer,
    CurriculumDetailSerializer,
    CurriculumGenerateSerializer,
    CurriculumListSerializer,
    TopicSerializer,
)
from apps.curriculum.models import (
    Curriculum,
    CurriculumCategory,
    CurriculumStep,
    CurriculumStepCourse,
    CurriculumStepProgress,
    CurriculumStepResource,
    LearningProgress,
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
        # success일 때만 저장한다. FK 조회와 transaction 처리는 저장 service가 담당한다.
        curriculum = save_ai_generated_curriculum(request.user, normalized_result)
        return Response(
            {
                "status": "success",
                "curriculum_id": curriculum.id,
                "message": "커리큘럼 생성이 완료되었습니다.",
                "curriculum": CurriculumDetailSerializer(curriculum).data,
            },
            status=status.HTTP_201_CREATED,
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
