from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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

from .serializers import (
    CurriculumCreateSerializer,
    CurriculumDetailSerializer,
    CurriculumListSerializer,
    TopicSerializer,
)


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
