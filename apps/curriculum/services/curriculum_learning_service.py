from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from apps.curriculum.models import (
    Curriculum,
    CurriculumStep,
    CurriculumStepProgress,
    LearningProgress,
    LearningSchedule,
)


class CurriculumLearningError(ValueError):
    """학습 상태 전환 요청이 현재 커리큘럼 상태와 맞지 않을 때 발생한다."""


def validate_curriculum_owner(curriculum, user):
    """요청 사용자가 커리큘럼 소유자인지 검증한다.

    학습 시작/일시정지/완료는 모두 DB 상태를 바꾸는 API다. 다른 사용자의
    curriculum id로 상태를 바꾸면 학습 이력이 섞이므로 service 진입점에서
    한 번 더 소유권을 확인한다.
    """
    if curriculum.user_id != user.id:
        raise PermissionDenied("Cannot access another user's curriculum.")


def get_next_pending_step(curriculum, user):
    """아직 완료되지 않은 가장 빠른 step을 반환한다.

    CurriculumStep은 AI가 만든 계획 데이터이고, 완료 여부는 실제 진행
    데이터인 CurriculumStepProgress 및 LearningProgress에 남는다. 그래서
    step_order 순서로 보되 이미 완료된 step id는 건너뛴다.
    """
    validate_curriculum_owner(curriculum, user)

    completed_step_ids = set(
        CurriculumStepProgress.objects.filter(
            curriculum=curriculum,
            status=CurriculumStepProgress.Status.COMPLETED,
        ).values_list("curriculum_step_id", flat=True)
    )
    completed_step_ids.update(
        LearningProgress.objects.filter(
            curriculum_step__curriculum=curriculum,
            status=LearningProgress.Status.COMPLETED,
        ).values_list("curriculum_step_id", flat=True)
    )

    return (
        CurriculumStep.objects.filter(curriculum=curriculum)
        .exclude(id__in=completed_step_ids)
        .order_by("step_order", "id")
        .first()
    )


def get_current_progress(curriculum, user):
    """현재 조정 대상인 가장 최근 진행 row를 찾는다.

    진행 중인 row를 우선 사용하고, 없다면 일시정지된 row를 사용한다. pause와
    complete API는 미래 step을 건드리지 않아야 하므로 이미 생성된 실제 진행
    row 중 가장 최근 row 하나만 대상으로 삼는다.
    """
    validate_curriculum_owner(curriculum, user)

    return (
        CurriculumStepProgress.objects.filter(
            curriculum=curriculum,
            status__in=[
                CurriculumStepProgress.Status.IN_PROGRESS,
                CurriculumStepProgress.Status.PAUSED,
            ],
        )
        .select_related("curriculum_step")
        .order_by("-updated_at", "-started_at", "-id")
        .first()
    )


def get_or_create_learning_schedule(step_progress, scheduled_date=None):
    """현재 step에 대한 미완료 schedule 하나를 재사용하거나 생성한다.

    start를 여러 번 눌러도 같은 step에 schedule이 중복 생성되지 않게 한다.
    schedule은 전체 커리큘럼 계획이 아니라 실제 학습을 시작한 step에만
    만들어지는 일정 데이터다.
    """
    step = step_progress.curriculum_step
    schedule = (
        LearningSchedule.objects.filter(
            curriculum_step=step,
            step_progress=step_progress,
        )
        .exclude(
            status__in=[
                LearningSchedule.Status.DONE,
                LearningSchedule.Status.CANCELLED,
            ]
        )
        .order_by("id")
        .first()
    )
    if schedule:
        return schedule

    schedule_count = LearningSchedule.objects.filter(
        curriculum_step__curriculum=step.curriculum,
    ).count()

    return LearningSchedule.objects.create(
        curriculum_step=step,
        step_progress=step_progress,
        week_no=schedule_count + 1,
        sequence_no=1,
        scheduled_date=scheduled_date or timezone.localdate(),
        planned_hours=step.estimated_hours or 1,
        status=LearningSchedule.Status.PLANNED,
    )


def get_or_create_learning_progress(step_progress, learning_schedule=None):
    """현재 step의 실제 학습 기록을 재사용하거나 생성한다.

    LearningProgress는 사용자가 실제로 학습을 수행한 기록이다. start 시점에는
    진행률 0의 IN_PROGRESS row로 만들고, pause/complete가 같은 row를 이어서
    갱신하도록 step_progress와 연결한다.
    """
    progress = (
        LearningProgress.objects.filter(
            curriculum_step=step_progress.curriculum_step,
            step_progress=step_progress,
        )
        .exclude(status=LearningProgress.Status.COMPLETED)
        .order_by("id")
        .first()
    )

    now = timezone.now()
    if progress:
        progress.status = LearningProgress.Status.IN_PROGRESS
        progress.progress_rate = progress.progress_rate or 0
        progress.learning_schedule = progress.learning_schedule or learning_schedule
        if not progress.started_at:
            progress.started_at = now
        progress.save(
            update_fields=[
                "status",
                "progress_rate",
                "learning_schedule",
                "started_at",
                "updated_at",
            ]
        )
        return progress

    return LearningProgress.objects.create(
        learning_schedule=learning_schedule,
        curriculum_step=step_progress.curriculum_step,
        step_progress=step_progress,
        status=LearningProgress.Status.IN_PROGRESS,
        progress_rate=0,
        studied_at=timezone.localdate(),
        started_at=now,
    )


def _get_or_create_step_progress(curriculum, step):
    step_progress, _ = CurriculumStepProgress.objects.get_or_create(
        curriculum=curriculum,
        curriculum_step=step,
        defaults={
            "status": CurriculumStepProgress.Status.IN_PROGRESS,
            "progress_rate": 0,
            "started_at": timezone.now(),
        },
    )
    return step_progress


def _has_next_pending_step(curriculum):
    return (
        CurriculumStep.objects.filter(curriculum=curriculum)
        .exclude(
            id__in=CurriculumStepProgress.objects.filter(
                curriculum=curriculum,
                status=CurriculumStepProgress.Status.COMPLETED,
            ).values("curriculum_step_id")
        )
        .exists()
    )


def _build_learning_response(curriculum, step=None, schedule=None, progress=None):
    step_progress = progress.step_progress if progress else None
    current_step = step or (step_progress.curriculum_step if step_progress else None)

    return {
        "curriculum_id": curriculum.id,
        "curriculum_status": curriculum.status,
        "current_step_id": current_step.id if current_step else None,
        "current_step_title": current_step.title if current_step else "",
        "learning_schedule_id": schedule.id if schedule else None,
        "learning_progress_id": progress.id if progress else None,
        "progress_status": progress.status if progress else "",
        "progress_percent": progress.progress_rate if progress else 0,
        "started_at": progress.started_at if progress else curriculum.started_at,
        "paused_at": step_progress.paused_at if step_progress else curriculum.paused_at,
        "completed_at": progress.completed_at if progress else curriculum.completed_at,
        "next_step_exists": _has_next_pending_step(curriculum),
    }


@transaction.atomic
def start_curriculum_learning(curriculum, user, scheduled_date=None):
    """커리큘럼의 현재 또는 다음 미진행 step 학습을 시작한다.

    이 함수는 학습 시작 버튼의 단일 진입점이다. 커리큘럼 전체 step에 대한
    schedule을 한 번에 만들지 않고, 지금 시작할 step 하나에 대해서만
    schedule/progress를 만든다.
    """
    validate_curriculum_owner(curriculum, user)
    curriculum = Curriculum.objects.select_for_update().get(id=curriculum.id)

    if curriculum.status == Curriculum.Status.COMPLETED:
        raise CurriculumLearningError("Completed curriculum cannot be started.")

    now = timezone.now()
    current_progress = get_current_progress(curriculum, user)
    if current_progress and curriculum.status in [
        Curriculum.Status.ACTIVE,
        Curriculum.Status.PAUSED,
    ]:
        current_progress.status = CurriculumStepProgress.Status.IN_PROGRESS
        current_progress.resumed_at = now
        if not current_progress.started_at:
            current_progress.started_at = now
        current_progress.save(
            update_fields=["status", "resumed_at", "started_at", "updated_at"]
        )
        schedule = get_or_create_learning_schedule(current_progress, scheduled_date)
        progress = get_or_create_learning_progress(current_progress, schedule)
        curriculum.status = Curriculum.Status.ACTIVE
        curriculum.current_step = current_progress.curriculum_step
        if not curriculum.started_at:
            curriculum.started_at = now
        curriculum.paused_at = None
        curriculum.save(
            update_fields=[
                "status",
                "current_step",
                "started_at",
                "paused_at",
                "updated_at",
            ]
        )
        return _build_learning_response(
            curriculum,
            current_progress.curriculum_step,
            schedule,
            progress,
        )

    next_step = get_next_pending_step(curriculum, user)
    if not next_step:
        curriculum.status = Curriculum.Status.COMPLETED
        curriculum.completed_at = curriculum.completed_at or now
        curriculum.save(update_fields=["status", "completed_at", "updated_at"])
        return _build_learning_response(curriculum)

    step_progress = _get_or_create_step_progress(curriculum, next_step)
    step_progress.status = CurriculumStepProgress.Status.IN_PROGRESS
    if not step_progress.started_at:
        step_progress.started_at = now
    step_progress.save(update_fields=["status", "started_at", "updated_at"])

    schedule = get_or_create_learning_schedule(step_progress, scheduled_date)
    progress = get_or_create_learning_progress(step_progress, schedule)

    curriculum.status = Curriculum.Status.ACTIVE
    curriculum.current_step = next_step
    if not curriculum.started_at:
        curriculum.started_at = now
    curriculum.paused_at = None
    curriculum.save(
        update_fields=[
            "status",
            "current_step",
            "started_at",
            "paused_at",
