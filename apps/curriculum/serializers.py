from rest_framework import serializers

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


class TopicSerializer(serializers.ModelSerializer):
    """학습 토픽 목록 API에서 사용하는 기본 Topic serializer다."""

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


class TargetTopicSerializer(serializers.ModelSerializer):
    """
    커리큘럼 단계가 목표로 삼는 학습 토픽을 내려주는 serializer다.

    상세 화면에서는 전체 Topic 모델의 관리용 필드보다, 사용자가 단계의 학습 주제를
    이해하는 데 필요한 최소 식별 정보만 필요하다.
    """

    class Meta:
        model = Topic
        fields = (
            "id",
            "name",
            "slug",
        )


class CurriculumCreateSerializer(serializers.Serializer):
    """
    POST /api/curriculums/ 요청 body를 검증한다.

    역할:
        클라이언트가 보낸 목표, 목표 기간, 주간 학습 가능 시간, 선호 학습 방식의 형식과
        범위만 검증한다.

    주의:
        UserProfile 기반 fallback은 serializer가 아니라 context service에서 처리한다.
        입력값 우선순위 규칙을 service 계층에 모아두기 위한 결정이다.
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

    목록 API에서는 단계, 자료, 강의 전체를 내려주지 않는다. 목록 화면은 커리큘럼 개요만
    필요하고, 상세 데이터는 /api/curriculums/{id}/에서 분리해서 조회한다.
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
    """
    생성 직후 응답에서 사용하는 기존 단계 serializer다.

    상세 API에는 더 풍부한 CurriculumStepDetailSerializer를 사용한다. 이 serializer는
    기존 생성 API 응답과 프론트 호환성을 위해 target_topic_name, topics 같은 편의 필드를
    유지한다.
    """

    target_topic = TargetTopicSerializer(read_only=True)
    target_topic_name = serializers.CharField(source="target_topic.name", read_only=True)
    status = serializers.SerializerMethodField()
    learning_objective = serializers.CharField(source="description", read_only=True)
    topics = serializers.SerializerMethodField()
    resources = serializers.SerializerMethodField()
    courses = serializers.SerializerMethodField()

    class Meta:
        model = CurriculumStep
        fields = (
            "id",
            "step_order",
            "title",
            "description",
            "target_topic",
            "target_topic_name",
            "difficulty_level",
            "estimated_hours",
            "prerequisite_note",
            "status",
            "learning_objective",
            "topics",
            "resources",
            "courses",
        )

    def get_status(self, step):
        """
        단계 진행 데이터가 없을 때 생성 응답 화면 표시용 임시 상태를 계산한다.

        상세 API는 CurriculumStepProgress를 사용하지만, 생성 직후에는 아직 진행 row를
        만들지 않으므로 기존 프론트 표시를 위해 첫 단계만 진행 중으로 보여준다.
        """
        if step.curriculum.status == Curriculum.Status.COMPLETED:
            return "COMPLETED"

        if step.step_order == 1:
            return "IN_PROGRESS"

        return "NOT_STARTED"

    def get_topics(self, step):
        """프론트의 토픽 chip 렌더링을 위해 target_topic 이름을 배열로 감싼다."""
        if not step.target_topic:
            return []

        return [step.target_topic.name]

    def get_resources(self, step):
        """생성 응답에서 단계에 연결된 추천 학습 자료를 간단한 객체 배열로 반환한다."""
        return [
            {
                "id": step_resource.learning_resource_id,
                "title": step_resource.learning_resource.title,
                "description": step_resource.learning_resource.description,
                "url": step_resource.learning_resource.url,
                "provider": step_resource.learning_resource.provider,
                "provider_name": step_resource.learning_resource.provider_name,
                "resource_type": step_resource.learning_resource.resource_type,
                "difficulty_level": step_resource.learning_resource.difficulty_level,
            }
            for step_resource in step.step_resources.select_related("learning_resource").order_by(
                "sort_order",
                "id",
            )
        ]

    def get_courses(self, step):
        """생성 응답에서 단계에 연결된 참고 강의를 간단한 객체 배열로 반환한다."""
        return [
            {
                "id": step_course.curriculum_course_id,
                "course_name": step_course.curriculum_course.course_name,
                "university_name": step_course.curriculum_course.university_name,
                "department_name": step_course.curriculum_course.department_name,
                "grade": step_course.curriculum_course.grade,
                "semester": step_course.curriculum_course.semester,
                "learning_objective": step_course.curriculum_course.learning_objective,
                "description": step_course.curriculum_course.description,
            }
            for step_course in step.step_courses.select_related("curriculum_course").order_by(
                "sort_order",
                "id",
            )
        ]


class CurriculumCategoryDetailSerializer(serializers.ModelSerializer):
    """
    커리큘럼 상세 응답에서 카테고리 연결 정보를 표현한다.

    CurriculumCategory는 연결 테이블이므로, 프론트에서 바로 사용할 수 있도록 실제
    Category의 id/name과 대표 카테고리 여부를 평평한 구조로 내려준다.
    """

    id = serializers.IntegerField(source="category.id", read_only=True)
    name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = CurriculumCategory
        fields = (
            "id",
            "name",
            "is_primary",
        )


class CurriculumStepResourceDetailSerializer(serializers.ModelSerializer):
    """
    단계별 추천 학습 자료를 상세 화면용 구조로 변환한다.

    provider_name과 difficulty_level은 이제 LearningResource의 실제 컬럼을 읽는다.
    provider는 과거 데이터와의 호환을 위해 모델에 유지하지만, 상세 API 응답의 주 키는
    provider_name이다.
    """

    id = serializers.IntegerField(source="learning_resource.id", read_only=True)
    title = serializers.CharField(source="learning_resource.title", read_only=True)
    resource_type = serializers.CharField(
        source="learning_resource.resource_type",
        read_only=True,
    )
    provider_name = serializers.CharField(
        source="learning_resource.provider_name",
        read_only=True,
    )
    difficulty_level = serializers.CharField(
        source="learning_resource.difficulty_level",
        read_only=True,
    )
    url = serializers.URLField(source="learning_resource.url", read_only=True)

    class Meta:
        model = CurriculumStepResource
        fields = (
            "id",
            "title",
            "resource_type",
            "provider_name",
            "difficulty_level",
            "url",
            "reason",
            "sort_order",
        )


class CurriculumStepCourseDetailSerializer(serializers.ModelSerializer):
    """
    단계별 추천 강의를 상세 화면용 구조로 변환한다.

    대학명, 학과명, 학년, 학기는 CurriculumCourse의 실제 컬럼을 그대로 읽는다.
    """

    id = serializers.IntegerField(source="curriculum_course.id", read_only=True)
    course_name = serializers.CharField(
        source="curriculum_course.course_name",
        read_only=True,
    )
    university_name = serializers.CharField(
        source="curriculum_course.university_name",
        read_only=True,
    )
    department_name = serializers.CharField(
        source="curriculum_course.department_name",
        read_only=True,
    )
    grade = serializers.IntegerField(source="curriculum_course.grade", read_only=True)
    semester = serializers.CharField(source="curriculum_course.semester", read_only=True)

    class Meta:
        model = CurriculumStepCourse
        fields = (
            "id",
            "course_name",
            "university_name",
            "department_name",
            "grade",
            "semester",
            "reason",
            "sort_order",
        )


class CurriculumStepProgressSerializer(serializers.ModelSerializer):
    """
    단계 진행 상태를 표현한다.

    상세 GET은 기존 진행 row를 읽기만 한다. 진행 row 생성, 일정 생성, 기록 생성은 별도
    API나 service에서 처리해야 한다.
    """

    curriculum_step_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = CurriculumStepProgress
        fields = (
            "id",
            "curriculum_step_id",
            "status",
            "started_at",
            "paused_at",
            "resumed_at",
            "completed_at",
            "progress_rate",
            "actual_minutes",
            "last_studied_at",
        )


class LearningScheduleSerializer(serializers.ModelSerializer):
    """현재 단계에 이미 생성된 학습 일정을 표현한다."""

    curriculum_step_id = serializers.IntegerField(read_only=True)
    step_progress_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = LearningSchedule
        fields = (
            "id",
            "curriculum_step_id",
            "step_progress_id",
            "week_no",
            "sequence_no",
            "scheduled_date",
            "planned_hours",
            "status",
        )


class LearningProgressSerializer(serializers.ModelSerializer):
    """현재 단계에 이미 기록된 실제 학습 기록을 표현한다."""

    learning_schedule_id = serializers.IntegerField(read_only=True)
    curriculum_step_id = serializers.IntegerField(read_only=True)
    step_progress_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = LearningProgress
        fields = (
            "id",
            "learning_schedule_id",
            "curriculum_step_id",
            "step_progress_id",
            "status",
            "actual_minutes",
            "progress_rate",
            "studied_at",
            "started_at",
            "completed_at",
            "memo",
        )


class CurriculumStepDetailSerializer(serializers.ModelSerializer):
    """
    커리큘럼 상세 화면에서 사용하는 단계 serializer다.

    각 단계의 기본 정보와 목표 토픽, 추천 자료, 추천 강의, 단계 진행 상태를 한 번에
    내려준다.
    """

    target_topic = TargetTopicSerializer(read_only=True)
    resources = serializers.SerializerMethodField()
    courses = serializers.SerializerMethodField()
    step_progress = serializers.SerializerMethodField()

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
            "resources",
            "courses",
            "step_progress",
        )

    def get_resources(self, step):
        """단계에 연결된 학습 자료를 sort_order 기준으로 반환한다."""
        step_resources = sorted(
            step.step_resources.all(),
            key=lambda step_resource: (step_resource.sort_order, step_resource.id),
        )
        return CurriculumStepResourceDetailSerializer(step_resources, many=True).data

    def get_courses(self, step):
        """단계에 연결된 강의 정보를 sort_order 기준으로 반환한다."""
        step_courses = sorted(
            step.step_courses.all(),
            key=lambda step_course: (step_course.sort_order, step_course.id),
        )
        return CurriculumStepCourseDetailSerializer(step_courses, many=True).data

    def get_step_progress(self, step):
        """단계에 연결된 진행 row가 있으면 반환하고, 없으면 null을 반환한다."""
        progress_records = sorted(
            step.progress_records.all(),
            key=lambda progress_record: progress_record.id,
        )
        if not progress_records:
            return None

        return CurriculumStepProgressSerializer(progress_records[0]).data


class CurriculumDetailSerializer(serializers.ModelSerializer):
    """
    GET /api/curriculums/{curriculum_id}/ 상세 응답 serializer다.

    포함 범위:
        - 커리큘럼 기본 정보
        - 연결된 카테고리
        - 전체 단계와 각 단계의 목표 토픽, 자료, 강의, 단계 진행 상태
        - 현재 단계 진행/일정/학습 기록

    중요한 점:
        상세 GET은 조회 전용이다. current_step_progress, current_step_schedules,
        current_step_learning_progresses는 이미 저장된 row만 읽고 새 row를 만들지 않는다.
    """

    current_step_id = serializers.IntegerField(read_only=True)
    categories = serializers.SerializerMethodField()
    steps = serializers.SerializerMethodField()
    current_step_progress = serializers.SerializerMethodField()
    current_step_schedules = serializers.SerializerMethodField()
    current_step_learning_progresses = serializers.SerializerMethodField()

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
            "categories",
            "steps",
            "current_step_id",
            "started_at",
            "paused_at",
            "completed_at",
            "current_step_progress",
            "current_step_schedules",
            "current_step_learning_progresses",
            "created_at",
            "updated_at",
        )

    def get_categories(self, curriculum):
        """커리큘럼에 연결된 카테고리를 대표 카테고리 우선으로 반환한다."""
        curriculum_categories = sorted(
            curriculum.curriculum_categories.all(),
            key=lambda curriculum_category: (
                not curriculum_category.is_primary,
                curriculum_category.id,
            ),
        )
        return CurriculumCategoryDetailSerializer(curriculum_categories, many=True).data

    def get_steps(self, curriculum):
        """커리큘럼 전체 단계를 step_order 기준으로 반환한다."""
        steps = sorted(
            curriculum.steps.all(),
            key=lambda step: (step.step_order, step.id),
        )
        return CurriculumStepDetailSerializer(steps, many=True).data

    def get_current_step_progress(self, curriculum):
        """
        현재 단계의 진행 row를 반환한다.

        DRAFT이거나 current_step이 아직 지정되지 않은 경우에는 null을 반환한다.
        """
        step_progress = self._get_current_step_progress(curriculum)
        if not step_progress:
            return None

        return CurriculumStepProgressSerializer(step_progress).data

    def get_current_step_schedules(self, curriculum):
        """현재 단계 진행 row에 연결된 학습 일정을 반환한다."""
        step_progress = self._get_current_step_progress(curriculum)
        if not step_progress:
            return []

        schedules = sorted(
            step_progress.schedules.all(),
            key=lambda schedule: (
                schedule.scheduled_date,
                schedule.sequence_no,
                schedule.id,
            ),
        )
        if curriculum.status == Curriculum.Status.PAUSED:
            schedules = [
                schedule
                for schedule in schedules
                if schedule.status
                not in [
                    LearningSchedule.Status.DONE,
                    LearningSchedule.Status.CANCELLED,
                ]
            ]

        return LearningScheduleSerializer(schedules, many=True).data

    def get_current_step_learning_progresses(self, curriculum):
        """현재 단계 진행 row에 연결된 실제 학습 기록을 반환한다."""
        step_progress = self._get_current_step_progress(curriculum)
        if not step_progress:
            return []

        learning_progresses = sorted(
            step_progress.learning_progresses.all(),
            key=lambda learning_progress: (
                learning_progress.studied_at.isoformat()
                if learning_progress.studied_at
                else "",
                learning_progress.id,
            ),
        )
        return LearningProgressSerializer(learning_progresses, many=True).data

    def _get_current_step_progress(self, curriculum):
        """
        현재 단계에 해당하는 진행 row를 찾는다.

        여러 serializer method에서 같은 조회 기준을 쓰기 때문에 한 곳에 모았다. prefetch된
        related manager가 있으면 그 캐시를 사용하고, 없으면 DB에서 조회한다.
        """
        if not curriculum.current_step_id:
            return None

        progress_records = sorted(
            curriculum.step_progresses.all(),
            key=lambda progress_record: progress_record.id,
        )
        for progress_record in progress_records:
            if progress_record.curriculum_step_id == curriculum.current_step_id:
                return progress_record

        return None
