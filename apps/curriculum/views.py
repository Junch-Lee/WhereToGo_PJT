from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import Topic
from apps.curriculum.models import Curriculum
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

    설계 의도:
        view에는 비즈니스 로직, 교육 데이터 검색, 생성기 호출, DB 저장 흐름을
        넣지 않는다. view는 인증, 입력 검증, service 호출, 응답 직렬화에만
        집중한다.
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
