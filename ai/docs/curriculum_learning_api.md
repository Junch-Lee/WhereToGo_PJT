# Curriculum Learning API

Existing project URLs use `curriculums`, so the learning APIs follow that style.

## Start

`POST /api/curriculums/{curriculum_id}/start/`

Request:

```json
{
  "scheduled_date": "2026-06-16"
}
```

Response:

```json
{
  "curriculum_id": 1,
  "curriculum_status": "ACTIVE",
  "current_step_id": 10,
  "current_step_title": "Django basics",
  "learning_schedule_id": 20,
  "learning_progress_id": 30,
  "progress_status": "IN_PROGRESS",
  "progress_percent": 0,
  "started_at": "2026-06-16T09:00:00Z",
  "paused_at": null,
  "completed_at": null,
  "next_step_exists": true
}
```

## Pause

`POST /api/curriculums/{curriculum_id}/pause/`

Pauses only the most recent current step progress and its incomplete learning progress.
It does not create or rewrite future step schedules.

## Complete

`POST /api/curriculums/{curriculum_id}/complete/`

MVP meaning: complete the current step, not force-complete the whole curriculum.
When that was the final pending step, the curriculum status becomes `COMPLETED`.

## State Transitions

- `DRAFT` -> `ACTIVE`: start first pending step.
- `PAUSED` -> `ACTIVE`: start resumes the current paused step.
- `ACTIVE` -> `PAUSED`: pause the current step only.
- `ACTIVE` or `PAUSED` -> `ACTIVE`: complete current step while another pending step exists.
- `ACTIVE` or `PAUSED` -> `COMPLETED`: complete current step when no pending step remains.
- `COMPLETED` -> start or pause: `400 Bad Request`.
