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
    """활성화된 학습 토픽 목록을 반환한다."""
    queryset = Topic.objects.filter(is_active=True).order_by("id")
    serializer = TopicSerializer(queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def curriculums(request):
    """
    인증된 사용자의 커리큘럼 목록 조회와 생성을 처리한다.

    GET:
        현재 로그인한 사용자가 소유한 Curriculum만 최신순으로 반환한다.

    POST:
        요청 body를 CurriculumCreateSerializer로 검증한 뒤, 실제 생성 흐름은
        create_curriculum_for_user service에 위임한다.
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
    인증된 사용자의 커리큘럼 상세 정보를 조회한다.

    보안 기준:
        URL의 curriculum_id가 존재하더라도 현재 로그인한 사용자의 커리큘럼이 아니면
        404를 반환한다. 이렇게 하면 다른 사용자의 커리큘럼 id를 추측해 접근하는 것을
        막을 수 있다.

    응답 범위:
        커리큘럼 기본 정보, 카테고리, 전체 단계, 단계별 목표 토픽, 추천 자료, 추천 강의를
        한 번에 반환한다. 현재 프로젝트에는 진행/일정/학습 기록 모델이 아직 없으므로
        관련 필드는 serializer에서 None 또는 빈 배열로 내려준다.

    주의:
        상세 GET은 조회 전용이다. 학습 일정이나 진행 기록을 새로 만들거나 수정하지 않는다.
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
