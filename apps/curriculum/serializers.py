from rest_framework import serializers

from apps.accounts.models import Topic
from apps.curriculum.models import Curriculum, CurriculumStep


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = (
            "id",
            "name",
            "parent_topic",
            "depth",
            "topic_type",
            "is_learning_unit",
            "is_assessable",
            "description",
        )


class CurriculumCreateSerializer(serializers.Serializer):
    """
    POST /api/curriculums/ 요청 body를 검증한다.

    역할:
        클라이언트가 보낸 goal, target_weeks, weekly_available_hours,
        preferred_learning_style의 형식과 범위만 검증한다.

    주의:
        UserProfile 기반 fallback은 serializer가 아니라 context service에서
        처리한다. 그래야 입력값 우선순위 규칙이 service 계층 한 곳에 모인다.
    """

    goal = serializers.CharField(required=True, allow_blank=False)
    target_weeks = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=52,
    )
    weekly_available_hours = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=80,
    )
    preferred_learning_style = serializers.ChoiceField(
        required=False,
        choices=["theory", "practice", "project", "video", "text", "balanced"],
    )


class CurriculumListSerializer(serializers.ModelSerializer):
    """
    GET /api/curriculums/ 목록 응답을 위한 가벼운 serializer다.

    역할:
        현재 로그인한 사용자의 커리큘럼 개요 정보를 내려준다.

    범위:
        목록 조회에서는 steps, resources, courses 전체를 내려주지 않는다. 목록
        API를 가볍게 유지하고, 상세 정보는 추후 상세 API에서 확장한다.
    """

    class Meta:
        model = Curriculum
        fields = (
            "id",
            "title",
            "goal",
            "status",
            "target_weeks",
            "weekly_available_hours",
            "preferred_learning_style",
            "difficulty_level",
            "recommendation_reason",
            "created_at",
            "updated_at",
        )


class CurriculumStepSerializer(serializers.ModelSerializer):
    target_topic = TopicSerializer(read_only=True)

    class Meta:
        model = CurriculumStep
        fields = (
            "id",
            "step_order",
            "title",
            "description",
            "target_topic",
            "difficulty_level",
            "estimated_hours",
            "prerequisite_note",
        )


class CurriculumDetailSerializer(serializers.ModelSerializer):
    """
    생성 직후 커리큘럼 응답을 위한 serializer다.

    역할:
        POST 생성 응답에서 부모 Curriculum 정보와 생성된 steps를 함께 보여준다.

    범위:
        이번 작업에서는 step resource/course 상세 응답은 제외한다. 연결 row는 DB에
        저장되지만, API 응답 구조를 불필요하게 키우지 않기 위해 step 중심으로
        반환한다.
    """

    steps = CurriculumStepSerializer(many=True, read_only=True)

    class Meta:
        model = Curriculum
        fields = (
            "id",
            "title",
            "goal",
            "status",
            "target_weeks",
            "weekly_available_hours",
            "preferred_learning_style",
            "difficulty_level",
            "recommendation_reason",
            "steps",
            "created_at",
            "updated_at",
        )
