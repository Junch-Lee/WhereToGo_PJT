from django.conf import settings
from django.db import models

from apps.accounts.models import Topic


class Category(models.Model):
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
    title = models.CharField(max_length=255)
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

    class Meta:
        db_table = "resource_topics"
        unique_together = ("learning_resource", "topic")


class CourseTopic(models.Model):
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

    class Meta:
        db_table = "course_topics"
        unique_together = ("curriculum_course", "topic")


class Curriculum(models.Model):
    class Status(models.TextChoices):
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
    class Status(models.TextChoices):
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
    class Status(models.TextChoices):
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
    class Status(models.TextChoices):
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
