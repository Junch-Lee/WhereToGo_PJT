from django.conf import settings
from django.db import models

from apps.accounts.models import Topic


class Category(models.Model):
    """
    커리큘럼과 학습 자료를 넓은 분야 단위로 묶는 분류 모델이다.

    상세 API에서는 CurriculumCategory를 통해 커리큘럼이 어떤 분야에 속하는지
    표시한다. slug는 외부 노출이나 검색용 식별자로 사용할 수 있다.
    """

    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "categories"

    def __str__(self):
        return self.name


class LearningResource(models.Model):
    """
    커리큘럼 단계에서 추천할 수 있는 외부 학습 자료를 저장한다.

    강의가 아닌 문서, 영상, 공식 가이드 같은 자료를 표현한다. 실제 단계 연결은
    CurriculumStepResource가 담당하며, 이 모델은 자료 자체의 메타데이터만 가진다.
    """

    title = models.CharField(max_length=255)
    lookup_key = models.CharField(max_length=100, unique=True, null=True, blank=True)
    description = models.TextField(blank=True)
    url = models.URLField(blank=True)
    provider = models.CharField(max_length=100, blank=True)
    provider_name = models.CharField(max_length=100, blank=True)
    resource_type = models.CharField(max_length=50, blank=True)
    difficulty_level = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "learning_resources"

    def __str__(self):
        return self.title


class CurriculumCourse(models.Model):
    """
    커리큘럼 단계에서 참고 과목으로 추천할 수 있는 강의/과목 데이터를 저장한다.

    LearningResource가 자료 단위라면, CurriculumCourse는 대학/학과/학기 같은
    교육 과정 맥락을 가진 과목 단위 데이터다. 단계 연결은 CurriculumStepCourse가 담당한다.
    """

    course_name = models.CharField(max_length=255)
    university_name = models.CharField(max_length=100, blank=True)
    department_name = models.CharField(max_length=100, blank=True)
    grade = models.PositiveSmallIntegerField(null=True, blank=True)
    semester = models.CharField(max_length=30, blank=True)
    learning_objective = models.TextField(blank=True)
    description = models.TextField(blank=True)
    source_row_number = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "curriculum_courses"

    def __str__(self):
        return self.course_name


class ResourceTopic(models.Model):
    """
    학습 자료와 토픽의 다대다 관계를 명시적으로 저장하는 연결 모델이다.

    목표 기반 검색에서 특정 Topic과 관련된 LearningResource를 찾을 때 사용할 수 있다.
    """

    learning_resource = models.ForeignKey(
        LearningResource,
        on_delete=models.CASCADE,
        related_name="resource_topics",
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="resource_topics",
    )
    relevance_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    extraction_method = models.CharField(max_length=50, blank=True)
    is_primary = models.BooleanField(default=False)
    matched_fields = models.TextField(blank=True)
    match_types = models.TextField(blank=True)
    link_type = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "resource_topics"
        unique_together = ("learning_resource", "topic")


class CourseTopic(models.Model):
    """
    참고 과목과 토픽의 다대다 관계를 명시적으로 저장하는 연결 모델이다.

    CurriculumCourse를 목표 토픽과 연결해 커리큘럼 생성 시 관련 과목을 찾기 쉽게 만든다.
    """

    curriculum_course = models.ForeignKey(
        CurriculumCourse,
        on_delete=models.CASCADE,
        related_name="course_topics",
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="course_topics",
    )
    relevance_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    extraction_method = models.CharField(max_length=50, blank=True)
    is_primary = models.BooleanField(default=False)
    matched_fields = models.TextField(blank=True)
    match_types = models.TextField(blank=True)
    link_type = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "course_topics"
        unique_together = ("curriculum_course", "topic")


class Curriculum(models.Model):
    """
    사용자가 생성한 하나의 커리큘럼 전체 정보를 저장한다.

    CurriculumStep은 AI가 만든 단계별 학습 계획이고, CurriculumStepProgress는 사용자의
    실제 단계별 수강 상태다. LearningSchedule과 LearningProgress는 현재 진행 중인 단계의
    일정과 실제 학습 기록을 관리한다.

    설계 의도:
        전체 step의 schedule을 커리큘럼 생성 시 한 번에 만들지 않는다. 사용자가 특정 step을
        시작할 때 해당 step의 일정만 생성하는 구조를 의도한다. 그래야 일시정지/재개 시 미래
        일정이 불필요하게 많이 무효화되는 문제를 줄일 수 있다.
    """

    class Status(models.TextChoices):
        # DRAFT: 커리큘럼은 생성됐지만 아직 학습을 시작하지 않은 상태
        # ACTIVE: 사용자가 현재 학습을 진행 중인 상태
        # PAUSED: 사용자가 학습을 일시정지한 상태
        # COMPLETED: 모든 단계 학습이 완료된 상태
        # CANCELLED: 사용자가 커리큘럼 진행을 중단한 상태
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        PAUSED = "PAUSED", "Paused"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="curricula",
    )
    interview_session = models.BigIntegerField(null=True, blank=True)
    title = models.CharField(max_length=255)
    goal = models.TextField()
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    target_weeks = models.PositiveSmallIntegerField(default=8)
    weekly_available_hours = models.PositiveSmallIntegerField(default=7)
    difficulty_level = models.CharField(max_length=30, default="beginner")
    preferred_learning_style = models.CharField(max_length=30, default="balanced")
    recommendation_reason = models.TextField(blank=True)
    current_step = models.ForeignKey(
        "CurriculumStep",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_curricula",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "curricula"
        ordering = ("-created_at", "-id")

    def __str__(self):
        return self.title


class CurriculumCategory(models.Model):
    """
    커리큘럼과 카테고리를 연결하는 모델이다.

    하나의 커리큘럼이 여러 분야와 관련될 수 있으므로 별도 연결 테이블로 관리한다.
    is_primary는 상세 화면에서 대표 분야를 먼저 보여주기 위한 플래그다.
    """

    curriculum = models.ForeignKey(
        Curriculum,
        on_delete=models.CASCADE,
        related_name="curriculum_categories",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="curriculum_categories",
    )
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = "curriculum_categories"
        unique_together = ("curriculum", "category")


class CurriculumStep(models.Model):
    """
    AI가 생성한 커리큘럼의 단계별 학습 계획이다.

    이 모델은 '무엇을 어떤 순서로 배울지'를 나타내는 계획 데이터다. 사용자가 실제로
    진행했는지, 얼마나 공부했는지는 CurriculumStepProgress와 LearningProgress에서 관리한다.
    """

    curriculum = models.ForeignKey(
        Curriculum,
        on_delete=models.CASCADE,
        related_name="steps",
    )
    step_order = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="curriculum_steps",
    )
    difficulty_level = models.CharField(max_length=30, default="beginner")
    estimated_hours = models.PositiveSmallIntegerField(default=0)
    prerequisite_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "curriculum_steps"
        ordering = ("step_order", "id")
        unique_together = ("curriculum", "step_order")

    def __str__(self):
        return self.title


class CurriculumStepResource(models.Model):
    """
    특정 커리큘럼 단계와 추천 학습 자료의 연결 정보를 저장한다.

    reason은 왜 이 자료가 해당 단계에 추천됐는지 설명하기 위한 필드이고, sort_order는
    상세 화면에서 자료를 안정적인 순서로 보여주기 위한 정렬 기준이다.
    """

    curriculum_step = models.ForeignKey(
        CurriculumStep,
        on_delete=models.CASCADE,
        related_name="step_resources",
    )
    learning_resource = models.ForeignKey(
        LearningResource,
        on_delete=models.CASCADE,
        related_name="curriculum_step_resources",
    )
    reason = models.TextField(blank=True)
    sort_order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = "curriculum_step_resources"
        unique_together = ("curriculum_step", "learning_resource")


class CurriculumStepCourse(models.Model):
    """
    특정 커리큘럼 단계와 참고 과목의 연결 정보를 저장한다.

    CurriculumStepResource와 같은 역할을 하지만, 대상이 일반 자료가 아니라 교육 과정/강의
    데이터라는 점이 다르다.
    """

    curriculum_step = models.ForeignKey(
        CurriculumStep,
        on_delete=models.CASCADE,
        related_name="step_courses",
    )
    curriculum_course = models.ForeignKey(
        CurriculumCourse,
        on_delete=models.CASCADE,
        related_name="curriculum_step_courses",
    )
    reason = models.TextField(blank=True)
    sort_order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = "curriculum_step_courses"
        unique_together = ("curriculum_step", "curriculum_course")


class CurriculumStepProgress(models.Model):
    """
    사용자의 단계별 실제 진행 상태를 저장한다.

    CurriculumStep이 계획이라면 이 모델은 사용자가 해당 step을 시작했는지, 일시정지했는지,
    완료했는지를 나타내는 실행 상태다. 상세 조회 API는 이 데이터를 읽기만 하며 새 진행 row를
    만들지 않는다.
    """

    class Status(models.TextChoices):
        # NOT_STARTED: 아직 해당 단계를 시작하지 않은 상태
        # IN_PROGRESS: 해당 단계를 진행 중인 상태
        # PAUSED: 해당 단계 진행이 일시정지된 상태
        # COMPLETED: 해당 단계가 완료된 상태
        # SKIPPED: 사용자가 해당 단계를 건너뛴 상태
        NOT_STARTED = "NOT_STARTED", "Not started"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        PAUSED = "PAUSED", "Paused"
        COMPLETED = "COMPLETED", "Completed"
        SKIPPED = "SKIPPED", "Skipped"

    curriculum = models.ForeignKey(
        Curriculum,
        on_delete=models.CASCADE,
        related_name="step_progresses",
    )
    curriculum_step = models.ForeignKey(
        CurriculumStep,
        on_delete=models.CASCADE,
        related_name="progress_records",
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.NOT_STARTED,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    resumed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress_rate = models.PositiveSmallIntegerField(default=0)
    actual_minutes = models.PositiveIntegerField(default=0)
    last_studied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "curriculum_step_progresses"
        unique_together = ("curriculum", "curriculum_step")

    def __str__(self):
        return f"{self.curriculum_step} - {self.status}"


class LearningSchedule(models.Model):
    """
    현재 진행 중인 단계에 대해 생성된 학습 일정이다.

    모든 단계의 일정을 처음부터 만들지 않고, step_progress가 생긴 단계의 일정만 연결한다.
    상세 조회 API에서는 이미 존재하는 일정만 반환하며, 일정 생성은 학습 시작/단계 시작 API의
    책임으로 분리한다.
    """

    class Status(models.TextChoices):
        # PLANNED: 아직 수행 전인 예정 일정
        # DONE: 사용자가 완료한 일정
        # CANCELLED: 취소된 일정
        # MISSED: 예정일에 수행하지 못한 일정
        # RESCHEDULED: 재조정된 일정
        PLANNED = "PLANNED", "Planned"
        DONE = "DONE", "Done"
        CANCELLED = "CANCELLED", "Cancelled"
        MISSED = "MISSED", "Missed"
        RESCHEDULED = "RESCHEDULED", "Rescheduled"

    curriculum_step = models.ForeignKey(
        CurriculumStep,
        on_delete=models.CASCADE,
        related_name="learning_schedules",
    )
    step_progress = models.ForeignKey(
        CurriculumStepProgress,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="schedules",
    )
    week_no = models.PositiveSmallIntegerField(default=1)
    sequence_no = models.PositiveSmallIntegerField(default=1)
    scheduled_date = models.DateField()
    planned_hours = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PLANNED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "learning_schedules"
        ordering = ("scheduled_date", "sequence_no", "id")

    def __str__(self):
        return f"{self.curriculum_step} - {self.sequence_no}"


class LearningProgress(models.Model):
    """
    사용자가 실제로 학습한 기록을 저장한다.

    LearningSchedule은 계획된 일정이고, LearningProgress는 사용자가 실제로 수행한 결과다.
    하나의 기록은 일정에 연결될 수도 있고, 일정 없이 수동 기록처럼 step에만 연결될 수도 있다.
    """

    class Status(models.TextChoices):
        # IN_PROGRESS: 사용자가 현재 수행 중인 학습 기록
        # PAUSED: 사용자가 일시정지한 학습 기록
        # COMPLETED: 해당 학습 기록을 완료 처리한 상태
        # PARTIAL: 일부만 수행한 과거 호환 상태
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        PAUSED = "PAUSED", "Paused"
        COMPLETED = "COMPLETED", "Completed"
        PARTIAL = "PARTIAL", "Partial"

    learning_schedule = models.ForeignKey(
        LearningSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="learning_progresses",
    )
    curriculum_step = models.ForeignKey(
        CurriculumStep,
        on_delete=models.CASCADE,
        related_name="learning_progresses",
    )
    step_progress = models.ForeignKey(
        CurriculumStepProgress,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="learning_progresses",
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.COMPLETED,
    )
    actual_minutes = models.PositiveIntegerField(default=0)
    progress_rate = models.PositiveSmallIntegerField(default=0)
    studied_at = models.DateField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    memo = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "learning_progresses"
        ordering = ("-studied_at", "-id")

    def __str__(self):
        return f"{self.curriculum_step} - {self.status}"
