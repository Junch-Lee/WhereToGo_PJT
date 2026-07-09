from rest_framework import serializers


class DashboardSummarySerializer(serializers.Serializer):
    total_curricula = serializers.IntegerField()
    draft_curricula = serializers.IntegerField()
    active_curricula = serializers.IntegerField()
    paused_curricula = serializers.IntegerField()
    completed_curricula = serializers.IntegerField()
    average_progress_percent = serializers.IntegerField()
    completed_step_count = serializers.IntegerField()
    total_step_count = serializers.IntegerField()
    total_estimated_minutes = serializers.IntegerField()
    schedule_adherence_percent = serializers.IntegerField(allow_null=True)


class LearningStepSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order = serializers.IntegerField()
    title = serializers.CharField()
    estimated_minutes = serializers.IntegerField()


class DashboardCurrentLearningSerializer(serializers.Serializer):
    curriculum_id = serializers.IntegerField()
    curriculum_title = serializers.CharField()
    curriculum_status = serializers.CharField()
    progress_percent = serializers.IntegerField()
    current_step = LearningStepSummarySerializer(allow_null=True)
    last_studied_at = serializers.DateTimeField(allow_null=True)
    next_action = serializers.CharField()


class DashboardRecentActivitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    activity_type = serializers.CharField()
    curriculum_id = serializers.IntegerField()
    curriculum_title = serializers.CharField()
    step_id = serializers.IntegerField()
    step_title = serializers.CharField()
    studied_at = serializers.DateTimeField(allow_null=True)
    actual_minutes = serializers.IntegerField()
    memo = serializers.CharField(allow_blank=True)


class LearningDashboardSerializer(serializers.Serializer):
    summary = DashboardSummarySerializer()
    current_learning = DashboardCurrentLearningSerializer(allow_null=True)
    recent_activities = DashboardRecentActivitySerializer(many=True)


class CurriculumProgressQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        required=False,
        choices=["NOT_STARTED", "IN_PROGRESS", "PAUSED", "COMPLETED"],
    )


class CurrentStepSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order = serializers.IntegerField()
    title = serializers.CharField()
    estimated_minutes = serializers.IntegerField()


class CurriculumProgressSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    status = serializers.CharField()
    progress_percent = serializers.IntegerField()
    completed_step_count = serializers.IntegerField()
    total_step_count = serializers.IntegerField()
    target_weeks = serializers.IntegerField()
    weekly_available_hours = serializers.IntegerField()
    updated_at = serializers.DateTimeField()
    last_studied_at = serializers.DateTimeField(allow_null=True)
    current_step = CurrentStepSerializer(allow_null=True, required=False)


class CurriculumProgressListSerializer(serializers.Serializer):
    results = CurriculumProgressSerializer(many=True)


class RoadmapQuerySerializer(serializers.Serializer):
    curriculum_id = serializers.IntegerField(required=True)


class CurrentLearningCurriculumSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    status = serializers.CharField()
    progress_percent = serializers.IntegerField()
    completed_step_count = serializers.IntegerField()
    total_step_count = serializers.IntegerField()
    target_weeks = serializers.IntegerField()
    weekly_available_hours = serializers.IntegerField()
    updated_at = serializers.DateTimeField()
    last_studied_at = serializers.DateTimeField(allow_null=True)


class TopicSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    slug = serializers.CharField()
    name = serializers.CharField()


class CurrentLearningStepSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    estimated_minutes = serializers.IntegerField()
    difficulty = serializers.CharField(allow_blank=True)
    target_topic = TopicSummarySerializer(allow_null=True)


class CurrentLearningResourceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    resource_type = serializers.CharField(allow_blank=True)
    provider = serializers.CharField(allow_blank=True)
    url = serializers.CharField(allow_blank=True)
    difficulty = serializers.CharField(allow_blank=True)


class CurrentLearningScheduleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    scheduled_date = serializers.DateField()
    planned_minutes = serializers.IntegerField()
    status = serializers.CharField()


class CurrentLearningDetailSerializer(serializers.Serializer):
    curriculum = CurrentLearningCurriculumSerializer()
    step = CurrentLearningStepSerializer(allow_null=True)
    resources = CurrentLearningResourceSerializer(many=True)
    schedule = CurrentLearningScheduleSerializer(allow_null=True)
    last_studied_at = serializers.DateTimeField(allow_null=True)
    next_action = serializers.CharField()


class CurrentLearningResponseSerializer(serializers.Serializer):
    current = CurrentLearningDetailSerializer(allow_null=True)


class RoadmapCurriculumSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    status = serializers.CharField()
    progress_percent = serializers.IntegerField()
    completed_step_count = serializers.IntegerField()
    total_step_count = serializers.IntegerField()
    target_weeks = serializers.IntegerField()
    weekly_available_hours = serializers.IntegerField()
    updated_at = serializers.DateTimeField()
    last_studied_at = serializers.DateTimeField(allow_null=True)


class RoadmapStepSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order = serializers.IntegerField()
    title = serializers.CharField()
    status = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    estimated_minutes = serializers.IntegerField()
    target_topic = TopicSummarySerializer(allow_null=True)
    completed_at = serializers.DateTimeField(allow_null=True)
    resource_count = serializers.IntegerField()
    prerequisite_note = serializers.CharField(allow_null=True)


class RoadmapSerializer(serializers.Serializer):
    curriculum = RoadmapCurriculumSerializer()
    steps = RoadmapStepSerializer(many=True)
