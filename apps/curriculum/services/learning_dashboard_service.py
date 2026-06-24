from datetime import date, datetime, time

from django.db.models import Prefetch
from django.utils import timezone

from apps.curriculum.models import (
    Curriculum,
    CurriculumStep,
    CurriculumStepProgress,
    CurriculumStepResource,
    LearningProgress,
    LearningSchedule,
)


ACTIVE_API_STATUS = "IN_PROGRESS"
PAUSED_API_STATUS = "PAUSED"
COMPLETED_API_STATUS = "COMPLETED"
NOT_STARTED_API_STATUS = "NOT_STARTED"


def hours_to_minutes(hours):
    """Step and schedule hour fields are stored as hours, but dashboard APIs expose minutes."""
    return int(hours or 0) * 60


def to_api_curriculum_status(status):
    """Map internal curriculum choices to the public dashboard status vocabulary."""
    return {
        Curriculum.Status.DRAFT: NOT_STARTED_API_STATUS,
        Curriculum.Status.ACTIVE: ACTIVE_API_STATUS,
        Curriculum.Status.PAUSED: PAUSED_API_STATUS,
        Curriculum.Status.COMPLETED: COMPLETED_API_STATUS,
    }.get(status, status)


def to_api_step_status(status):
    """Map step progress choices to the compact roadmap status vocabulary."""
    if status == CurriculumStepProgress.Status.COMPLETED:
        return COMPLETED_API_STATUS
    if status in [
        CurriculumStepProgress.Status.IN_PROGRESS,
        CurriculumStepProgress.Status.PAUSED,
    ]:
        return ACTIVE_API_STATUS
    if status == CurriculumStepProgress.Status.SKIPPED:
        return "SKIPPED"
    return "PENDING"


def build_learning_dashboard(user):
    """Return summary, current-learning, and recent-activity data for one authenticated user.

    The service always starts from a user-scoped curriculum queryset so another user's
    learning data cannot leak through a dashboard aggregate. Relationships used by the
    four dashboard endpoints are prefetched once here to avoid curriculum-by-curriculum
    detail API calls and repeated ORM queries inside serializers.
    """
    curricula = list(_user_curricula_queryset(user))

    return {
        "summary": _build_summary(curricula),
        "current_learning": _build_current_learning(_select_current_curriculum(curricula)),
        "recent_activities": _build_recent_activities(user, curricula, limit=5),
    }


def build_curriculum_progress_list(user, status_filter=None):
    """Return progress-card data for all curricula owned by the user.

    ``status_filter`` uses the public API status values. Invalid values are rejected in
    the view serializer before this function is called.
    """
    items = [_build_curriculum_progress_item(curriculum) for curriculum in _user_curricula_queryset(user)]
    if status_filter:
        items = [item for item in items if item["status"] == status_filter]

    return {"results": sorted(items, key=_curriculum_progress_sort_key)}


def build_current_learning(user):
    """Return the richest current-learning card payload, or ``{"current": None}``.

    Active curricula are preferred over paused curricula. Draft and completed curricula
    are intentionally not selected as current work because they do not represent an
    ongoing learning session.
    """
    curriculum = _select_current_curriculum(list(_user_curricula_queryset(user)))
    if not curriculum:
        return {"current": None}

    return {"current": _build_current_learning_detail(curriculum)}


def build_roadmap(curriculum):
    """Return a lightweight step timeline for a curriculum already scoped to the user."""
    return {
        "curriculum": _build_curriculum_progress_item(curriculum, include_current_step=False),
        "steps": [_build_roadmap_step(step, _progress_for_step(curriculum, step.id)) for step in _steps(curriculum)],
    }


def get_user_curriculum_for_dashboard(user, curriculum_id):
    """Fetch one curriculum with dashboard prefetches while preserving 404-on-foreign access."""
    return _user_curricula_queryset(user).filter(id=curriculum_id).first()


def _user_curricula_queryset(user):
    step_progress_queryset = (
        CurriculumStepProgress.objects.select_related("curriculum_step")
        .prefetch_related(
            Prefetch(
                "schedules",
                queryset=LearningSchedule.objects.order_by("scheduled_date", "sequence_no", "id"),
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
                queryset=CurriculumStepResource.objects.select_related("learning_resource").order_by(
                    "sort_order",
                    "id",
                ),
            ),
            "step_courses",
        )
        .order_by("step_order", "id")
    )

    return (
        Curriculum.objects.filter(user=user)
        .select_related("current_step")
        .prefetch_related(
            Prefetch("steps", queryset=step_queryset),
            Prefetch("step_progresses", queryset=step_progress_queryset),
        )
        .order_by("-updated_at", "-id")
    )


def _build_summary(curricula):
    completed_step_count = sum(_completed_step_count(curriculum) for curriculum in curricula)
    total_step_count = sum(len(_steps(curriculum)) for curriculum in curricula)
    progress_targets = [
        _progress_percent(curriculum)
        for curriculum in curricula
        if curriculum.status != Curriculum.Status.DRAFT
    ]

    return {
        "total_curricula": len(curricula),
        "draft_curricula": sum(1 for curriculum in curricula if curriculum.status == Curriculum.Status.DRAFT),
        "active_curricula": sum(1 for curriculum in curricula if curriculum.status == Curriculum.Status.ACTIVE),
        "paused_curricula": sum(1 for curriculum in curricula if curriculum.status == Curriculum.Status.PAUSED),
        "completed_curricula": sum(1 for curriculum in curricula if curriculum.status == Curriculum.Status.COMPLETED),
        "average_progress_percent": round(sum(progress_targets) / len(progress_targets)) if progress_targets else 0,
        "completed_step_count": completed_step_count,
        "total_step_count": total_step_count,
        "total_estimated_minutes": sum(_estimated_minutes(curriculum) for curriculum in curricula),
        "schedule_adherence_percent": _schedule_adherence_percent(curricula),
    }


def _build_curriculum_progress_item(curriculum, include_current_step=True):
    item = {
        "id": curriculum.id,
        "title": curriculum.title,
        "status": to_api_curriculum_status(curriculum.status),
        "progress_percent": _progress_percent(curriculum),
        "completed_step_count": _completed_step_count(curriculum),
        "total_step_count": len(_steps(curriculum)),
        "target_weeks": curriculum.target_weeks,
        "weekly_available_hours": curriculum.weekly_available_hours,
        "updated_at": curriculum.updated_at,
        "last_studied_at": _last_studied_at(curriculum),
    }
    if include_current_step:
        item["current_step"] = _build_step_summary(_select_current_step(curriculum))

    return item


def _build_current_learning(curriculum):
    if not curriculum:
        return None

    step = _select_current_step(curriculum)
    return {
        "curriculum_id": curriculum.id,
        "curriculum_title": curriculum.title,
        "curriculum_status": to_api_curriculum_status(curriculum.status),
        "progress_percent": _progress_percent(curriculum),
        "current_step": _build_step_summary(step),
        "last_studied_at": _last_studied_at(curriculum),
        "next_action": _next_action(curriculum),
    }


def _build_current_learning_detail(curriculum):
    step = _select_current_step(curriculum)
    resources = _current_step_resources(step)
    schedule = _select_current_schedule(curriculum, step)

    return {
        "curriculum": _build_curriculum_progress_item(curriculum, include_current_step=False),
        "step": _build_step_detail(step),
        "resources": resources,
        "schedule": _build_schedule(schedule),
        "last_studied_at": _last_studied_at(curriculum),
        "next_action": _next_action(curriculum),
    }


def _build_recent_activities(user, curricula, limit=5):
    """Build recent activity rows from stored progress rows without fabricating events."""
    progress_rows = (
        LearningProgress.objects.filter(curriculum_step__curriculum__user=user)
        .select_related("curriculum_step", "curriculum_step__curriculum")
        .exclude(studied_at__isnull=True)
        .order_by("-studied_at", "-id")[:limit]
    )
    activities = [
        {
            "id": progress.id,
            "activity_type": "STEP_COMPLETED"
            if progress.status == LearningProgress.Status.COMPLETED
            else "STEP_PROGRESS_RECORDED",
            "curriculum_id": progress.curriculum_step.curriculum_id,
            "curriculum_title": progress.curriculum_step.curriculum.title,
            "step_id": progress.curriculum_step_id,
            "step_title": progress.curriculum_step.title,
            "studied_at": _date_to_datetime(progress.studied_at),
            "actual_minutes": progress.actual_minutes,
            "memo": progress.memo,
        }
        for progress in progress_rows
    ]

    if activities:
        return activities

    fallback_rows = []
    for curriculum in curricula:
        for progress in _step_progresses(curriculum):
            studied_at = progress.completed_at or progress.last_studied_at
            if not studied_at:
                continue
            fallback_rows.append(
                {
                    "id": progress.id,
                    "activity_type": "STEP_COMPLETED"
                    if progress.status == CurriculumStepProgress.Status.COMPLETED
                    else "STEP_PROGRESS_RECORDED",
                    "curriculum_id": curriculum.id,
                    "curriculum_title": curriculum.title,
                    "step_id": progress.curriculum_step_id,
                    "step_title": progress.curriculum_step.title,
                    "studied_at": studied_at,
                    "actual_minutes": progress.actual_minutes,
                    "memo": "",
                }
            )

    return sorted(fallback_rows, key=lambda item: item["studied_at"], reverse=True)[:limit]


def _build_roadmap_step(step, progress):
    status = to_api_step_status(progress.status if progress else None)
    completed_at = progress.completed_at if progress and progress.status == CurriculumStepProgress.Status.COMPLETED else None

    return {
        "id": step.id,
        "order": step.step_order,
        "title": step.title,
        "status": status,
        "description": step.description,
        "estimated_minutes": hours_to_minutes(step.estimated_hours),
        "target_topic": _build_topic(step.target_topic),
        "completed_at": completed_at,
        "resource_count": len(list(step.step_resources.all())),
        "prerequisite_note": step.prerequisite_note or None,
    }


def _build_step_summary(step):
    if not step:
        return None

    return {
        "id": step.id,
        "order": step.step_order,
        "title": step.title,
        "estimated_minutes": hours_to_minutes(step.estimated_hours),
    }


def _build_step_detail(step):
    if not step:
        return None

    return {
        "id": step.id,
        "order": step.step_order,
        "title": step.title,
        "description": step.description,
        "estimated_minutes": hours_to_minutes(step.estimated_hours),
        "difficulty": step.difficulty_level,
        "target_topic": _build_topic(step.target_topic),
    }


def _build_topic(topic):
    if not topic:
        return None

    return {
        "id": topic.id,
        "slug": topic.slug,
        "name": topic.name,
    }


def _build_schedule(schedule):
    if not schedule:
        return None

    return {
        "id": schedule.id,
        "scheduled_date": schedule.scheduled_date,
        "planned_minutes": hours_to_minutes(schedule.planned_hours),
        "status": schedule.status,
    }


def _current_step_resources(step, limit=3):
    if not step:
        return []

    resources = []
    seen_ids = set()
    for step_resource in step.step_resources.all():
        resource = step_resource.learning_resource
        if resource.id in seen_ids:
            continue
        seen_ids.add(resource.id)
        resources.append(
            {
                "id": resource.id,
                "title": resource.title,
                "resource_type": resource.resource_type,
                "provider": resource.provider_name or resource.provider,
                "url": resource.url,
                "difficulty": resource.difficulty_level,
            }
        )
        if len(resources) >= limit:
            break

    return resources


def _select_current_curriculum(curricula):
    candidates = [
        curriculum
        for curriculum in curricula
        if curriculum.status in [Curriculum.Status.ACTIVE, Curriculum.Status.PAUSED]
    ]
    if not candidates:
        return None

    return sorted(candidates, key=_current_curriculum_sort_key)[0]


def _current_curriculum_sort_key(curriculum):
    active_rank = 0 if curriculum.status == Curriculum.Status.ACTIVE else 1
    studied_at = _last_studied_at(curriculum) or curriculum.updated_at or curriculum.created_at
    timestamp = studied_at.timestamp() if studied_at else 0
    return (active_rank, -timestamp, -curriculum.id)


def _select_current_step(curriculum):
    if not curriculum:
        return None

    for progress in _step_progresses(curriculum):
        if progress.status in [
            CurriculumStepProgress.Status.IN_PROGRESS,
            CurriculumStepProgress.Status.PAUSED,
        ]:
            return progress.curriculum_step

    if curriculum.current_step_id:
        for step in _steps(curriculum):
            if step.id == curriculum.current_step_id:
                return step

    completed_step_ids = {
        progress.curriculum_step_id
        for progress in _step_progresses(curriculum)
        if progress.status == CurriculumStepProgress.Status.COMPLETED
    }
    for step in _steps(curriculum):
        if step.id not in completed_step_ids:
            return step

    return None


def _select_current_schedule(curriculum, step):
    if not step:
        return None

    progress = _progress_for_step(curriculum, step.id)
    if not progress:
        return None

    schedules = [
        schedule
        for schedule in progress.schedules.all()
        if schedule.status not in [LearningSchedule.Status.DONE, LearningSchedule.Status.CANCELLED]
    ]
    if not schedules:
        return None

    today = timezone.localdate()
    today_schedules = [schedule for schedule in schedules if schedule.scheduled_date == today]
    if today_schedules:
        return sorted(today_schedules, key=lambda schedule: (schedule.sequence_no, schedule.id))[0]

    future_schedules = [schedule for schedule in schedules if schedule.scheduled_date > today]
    if future_schedules:
        return sorted(future_schedules, key=lambda schedule: (schedule.scheduled_date, schedule.sequence_no, schedule.id))[0]

    return sorted(schedules, key=lambda schedule: (schedule.scheduled_date, schedule.sequence_no, schedule.id))[0]


def _progress_percent(curriculum):
    steps = _steps(curriculum)
    if not steps:
        return 0
    if curriculum.status == Curriculum.Status.COMPLETED:
        return 100

    return round(_completed_step_count(curriculum) / len(steps) * 100)


def _completed_step_count(curriculum):
    return sum(
        1
        for progress in _step_progresses(curriculum)
        if progress.status == CurriculumStepProgress.Status.COMPLETED
    )


def _estimated_minutes(curriculum):
    return sum(hours_to_minutes(step.estimated_hours) for step in _steps(curriculum))


def _schedule_adherence_percent(curricula):
    today = timezone.localdate()
    eligible = []
    for curriculum in curricula:
        for progress in _step_progresses(curriculum):
            eligible.extend(
                schedule
                for schedule in progress.schedules.all()
                if schedule.scheduled_date <= today
                and schedule.status != LearningSchedule.Status.CANCELLED
            )

    if not eligible:
        return None

    done_count = sum(1 for schedule in eligible if schedule.status == LearningSchedule.Status.DONE)
    return round(done_count / len(eligible) * 100)


def _last_studied_at(curriculum):
    candidates = []
    for progress in _step_progresses(curriculum):
        candidates.extend(
            _date_to_datetime(learning_progress.studied_at)
            for learning_progress in progress.learning_progresses.all()
            if learning_progress.studied_at
        )
        if progress.last_studied_at:
            candidates.append(progress.last_studied_at)
        if progress.completed_at:
            candidates.append(progress.completed_at)

    return max(candidates) if candidates else None


def _next_action(curriculum):
    if curriculum.status == Curriculum.Status.PAUSED:
        return "RESUME"
    if curriculum.status == Curriculum.Status.ACTIVE:
        return "CONTINUE"
    return "START"


def _curriculum_progress_sort_key(item):
    rank = {
        ACTIVE_API_STATUS: 0,
        PAUSED_API_STATUS: 1,
        NOT_STARTED_API_STATUS: 2,
        COMPLETED_API_STATUS: 3,
    }.get(item["status"], 4)
    latest = item["last_studied_at"] or item["updated_at"]
    timestamp = latest.timestamp() if latest else 0
    return (rank, -timestamp, -item["id"])


def _steps(curriculum):
    return list(curriculum.steps.all())


def _step_progresses(curriculum):
    return list(curriculum.step_progresses.all())


def _progress_for_step(curriculum, step_id):
    for progress in _step_progresses(curriculum):
        if progress.curriculum_step_id == step_id:
            return progress

    return None


def _date_to_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return timezone.make_aware(datetime.combine(value, time.min))

    return None
