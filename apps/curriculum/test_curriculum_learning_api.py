from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.curriculum.models import (
    Curriculum,
    CurriculumStep,
    CurriculumStepProgress,
    LearningProgress,
    LearningSchedule,
)
from apps.curriculum.services.curriculum_learning_service import (
    start_curriculum_learning,
)


User = get_user_model()


@override_settings(ROOT_URLCONF="config.urls")
class CurriculumLearningAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="learner@example.com",
            password="password123",
            nickname="learner",
            agree_terms=True,
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="password123",
            nickname="other",
            agree_terms=True,
        )
        self.curriculum = Curriculum.objects.create(
            user=self.user,
            title="Backend roadmap",
            goal="Learn Django",
            target_weeks=4,
            weekly_available_hours=7,
        )
        self.first_step = CurriculumStep.objects.create(
            curriculum=self.curriculum,
            step_order=1,
            title="Django basics",
            description="Models and views",
            estimated_hours=3,
        )
        self.second_step = CurriculumStep.objects.create(
            curriculum=self.curriculum,
            step_order=2,
            title="DRF basics",
            description="Serializers and APIs",
            estimated_hours=4,
        )

    def _login(self):
        self.client.force_authenticate(user=self.user)

    def _url(self, action, curriculum=None):
        curriculum = curriculum or self.curriculum
        return f"/api/curriculums/{curriculum.id}/{action}/"

    def _detail_url(self, curriculum=None):
        curriculum = curriculum or self.curriculum
        return f"/api/curriculums/{curriculum.id}/"

    def _step_complete_url(self, step, curriculum=None):
        curriculum = curriculum or self.curriculum
        return f"/api/curriculums/{curriculum.id}/steps/{step.id}/complete/"

    def _start(self):
        self._login()
        return self.client.post(self._url("start"), {}, format="json")

    def test_start_creates_learning_schedule_for_first_pending_step(self):
        response = self._start()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schedule = LearningSchedule.objects.get()
        self.assertEqual(schedule.curriculum_step, self.first_step)
        self.assertEqual(schedule.status, LearningSchedule.Status.PLANNED)
        self.assertEqual(response.data["learning_schedule_id"], schedule.id)

    def test_start_creates_learning_progress_for_first_pending_step(self):
        response = self._start()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        progress = LearningProgress.objects.get()
        self.assertEqual(progress.curriculum_step, self.first_step)
        self.assertEqual(progress.status, LearningProgress.Status.IN_PROGRESS)
        self.assertEqual(progress.progress_rate, 0)
        self.assertEqual(response.data["learning_progress_id"], progress.id)

    def test_start_skips_completed_step_and_starts_next_pending_step(self):
        CurriculumStepProgress.objects.create(
            curriculum=self.curriculum,
            curriculum_step=self.first_step,
            status=CurriculumStepProgress.Status.COMPLETED,
            progress_rate=100,
        )

        response = self._start()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["current_step_id"], self.second_step.id)
        self.assertEqual(LearningSchedule.objects.get().curriculum_step, self.second_step)

    def test_start_does_not_duplicate_schedule_or_progress_when_already_active(self):
        self._start()

        response = self._start()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(LearningSchedule.objects.count(), 1)
        self.assertEqual(LearningProgress.objects.count(), 1)

    def test_start_paused_curriculum_resumes_current_step(self):
        self._start()
        self.client.post(self._url("pause"), {}, format="json")

        response = self.client.post(self._url("start"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.curriculum.refresh_from_db()
        self.assertEqual(self.curriculum.status, Curriculum.Status.ACTIVE)
        self.assertEqual(LearningProgress.objects.get().status, LearningProgress.Status.IN_PROGRESS)

    def test_start_completed_curriculum_returns_400(self):
        self.curriculum.status = Curriculum.Status.COMPLETED
        self.curriculum.save(update_fields=["status", "updated_at"])

        response = self._start()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pause_active_curriculum_pauses_current_progress(self):
        self._start()

        response = self.client.post(self._url("pause"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.curriculum.refresh_from_db()
        step_progress = CurriculumStepProgress.objects.get()
        learning_progress = LearningProgress.objects.get()
        self.assertEqual(self.curriculum.status, Curriculum.Status.PAUSED)
        self.assertEqual(step_progress.status, CurriculumStepProgress.Status.PAUSED)
        self.assertEqual(learning_progress.status, LearningProgress.Status.PAUSED)

    def test_pause_does_not_create_or_modify_future_step_schedule(self):
        self._start()

        response = self.client.post(self._url("pause"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(LearningSchedule.objects.count(), 1)
        self.assertFalse(
            LearningSchedule.objects.filter(curriculum_step=self.second_step).exists()
        )

    def test_pause_not_started_curriculum_returns_400(self):
        self._login()

        response = self.client.post(self._url("pause"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resume_paused_curriculum_returns_detail_with_in_progress_status(self):
        self._start()
        self.client.post(self._url("pause"), {}, format="json")

        response = self.client.post(self._url("resume"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.curriculum.refresh_from_db()
        self.assertEqual(self.curriculum.status, Curriculum.Status.ACTIVE)
        self.assertEqual(self.curriculum.current_step, self.first_step)
        self.assertEqual(response.data["status"], "IN_PROGRESS")
        self.assertEqual(response.data["current_step_id"], self.first_step.id)

    def test_resume_draft_curriculum_returns_400(self):
        self._login()

        response = self.client.post(self._url("resume"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.curriculum.refresh_from_db()
        self.assertEqual(self.curriculum.status, Curriculum.Status.DRAFT)

    def test_resume_active_curriculum_returns_400(self):
        self._start()

        response = self.client.post(self._url("resume"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.curriculum.refresh_from_db()
        self.assertEqual(self.curriculum.status, Curriculum.Status.ACTIVE)

    def test_resume_completed_curriculum_returns_400(self):
        self._start()
        self.client.post(self._url("complete"), {}, format="json")
        self.client.post(self._url("complete"), {}, format="json")

        response = self.client.post(self._url("resume"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.curriculum.refresh_from_db()
        self.assertEqual(self.curriculum.status, Curriculum.Status.COMPLETED)

    def test_complete_current_step_marks_completed_progress_to_100(self):
        self._start()

        response = self.client.post(self._url("complete"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        progress = LearningProgress.objects.get(curriculum_step=self.first_step)
        self.assertEqual(progress.progress_rate, 100)
        self.assertEqual(progress.status, LearningProgress.Status.COMPLETED)

    def test_complete_current_step_marks_schedule_done(self):
        self._start()

        response = self.client.post(self._url("complete"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schedule = LearningSchedule.objects.get(curriculum_step=self.first_step)
        self.assertEqual(schedule.status, LearningSchedule.Status.DONE)

    def test_complete_paused_curriculum_returns_400_without_state_change(self):
        self._start()
        self.client.post(self._url("pause"), {}, format="json")

        response = self.client.post(self._url("complete"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.curriculum.refresh_from_db()
        step_progress = CurriculumStepProgress.objects.get(curriculum_step=self.first_step)
        self.assertEqual(self.curriculum.status, Curriculum.Status.PAUSED)
        self.assertEqual(self.curriculum.current_step, self.first_step)
        self.assertEqual(step_progress.status, CurriculumStepProgress.Status.PAUSED)

    def test_complete_draft_curriculum_returns_400_without_progress(self):
        self._login()

        response = self.client.post(self._url("complete"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.curriculum.refresh_from_db()
        self.assertEqual(self.curriculum.status, Curriculum.Status.DRAFT)
        self.assertFalse(CurriculumStepProgress.objects.exists())

    def test_complete_completed_curriculum_returns_400_without_state_change(self):
        self._start()
        self.client.post(self._url("complete"), {}, format="json")
        self.client.post(self._url("complete"), {}, format="json")

        response = self.client.post(self._url("complete"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.curriculum.refresh_from_db()
        self.assertEqual(self.curriculum.status, Curriculum.Status.COMPLETED)
        self.assertIsNone(self.curriculum.current_step)

    def test_complete_current_step_automatically_starts_next_step(self):
        self._start()

        response = self.client.post(self._url("complete"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.curriculum.refresh_from_db()
        first_progress = CurriculumStepProgress.objects.get(curriculum_step=self.first_step)
        second_progress = CurriculumStepProgress.objects.get(curriculum_step=self.second_step)
        self.assertEqual(first_progress.status, CurriculumStepProgress.Status.COMPLETED)
        self.assertEqual(second_progress.status, CurriculumStepProgress.Status.IN_PROGRESS)
        self.assertEqual(self.curriculum.current_step, self.second_step)
        self.assertEqual(self.curriculum.status, Curriculum.Status.ACTIVE)

    def test_complete_current_step_by_step_api_succeeds(self):
        self._start()

        response = self.client.post(
            self._step_complete_url(self.first_step),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.curriculum.refresh_from_db()
        first_progress = CurriculumStepProgress.objects.get(curriculum_step=self.first_step)
        second_progress = CurriculumStepProgress.objects.get(curriculum_step=self.second_step)
        self.assertEqual(first_progress.status, CurriculumStepProgress.Status.COMPLETED)
        self.assertEqual(second_progress.status, CurriculumStepProgress.Status.IN_PROGRESS)
        self.assertEqual(self.curriculum.current_step, self.second_step)
        self.assertEqual(response.data["status"], "IN_PROGRESS")
        self.assertEqual(response.data["current_step"]["id"], self.second_step.id)

    def test_complete_non_current_step_by_step_api_returns_400(self):
        self._start()

        response = self.client.post(
            self._step_complete_url(self.second_step),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.curriculum.refresh_from_db()
        self.assertEqual(self.curriculum.current_step, self.first_step)
        self.assertFalse(
            CurriculumStepProgress.objects.filter(
                curriculum_step=self.second_step,
                status=CurriculumStepProgress.Status.COMPLETED,
            ).exists()
        )

    def test_complete_already_completed_step_by_step_api_returns_400(self):
        self._start()
        self.client.post(self._step_complete_url(self.first_step), {}, format="json")

        response = self.client.post(
            self._step_complete_url(self.first_step),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.curriculum.refresh_from_db()
        self.assertEqual(self.curriculum.current_step, self.second_step)
        self.assertEqual(self.curriculum.status, Curriculum.Status.ACTIVE)

    def test_complete_step_from_other_curriculum_returns_404(self):
        other_curriculum = Curriculum.objects.create(
            user=self.user,
            title="Other roadmap",
            goal="Other goal",
        )
        other_step = CurriculumStep.objects.create(
            curriculum=other_curriculum,
            step_order=1,
            title="Other step",
            description="Other step",
        )
        self._start()

        response = self.client.post(
            self._step_complete_url(other_step),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.curriculum.refresh_from_db()
        other_curriculum.refresh_from_db()
        self.assertEqual(self.curriculum.status, Curriculum.Status.ACTIVE)
        self.assertEqual(other_curriculum.status, Curriculum.Status.DRAFT)

    def test_other_user_cannot_resume_or_complete_step(self):
        self._start()
        self.client.post(self._url("pause"), {}, format="json")
        self.client.force_authenticate(user=self.other_user)

        resume_response = self.client.post(self._url("resume"), {}, format="json")
        step_response = self.client.post(
            self._step_complete_url(self.first_step),
            {},
            format="json",
        )

        self.assertEqual(resume_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(step_response.status_code, status.HTTP_404_NOT_FOUND)
        self.curriculum.refresh_from_db()
        self.assertEqual(self.curriculum.status, Curriculum.Status.PAUSED)
        self.assertEqual(self.curriculum.current_step, self.first_step)

    def test_complete_all_steps_marks_curriculum_completed(self):
        self._start()
        self.client.post(self._url("complete"), {}, format="json")

        response = self.client.post(self._url("complete"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.curriculum.refresh_from_db()
        self.assertEqual(self.curriculum.status, Curriculum.Status.COMPLETED)
        self.assertIsNone(self.curriculum.current_step)
        self.assertFalse(response.data["next_step_exists"])

        detail_response = self.client.get(self._detail_url(), format="json")
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data["progress_percent"], 100)
        self.assertEqual(
            detail_response.data["completed_step_count"],
            detail_response.data["total_step_count"],
        )

    def test_curriculum_detail_includes_progress_summary_fields(self):
        third_step = CurriculumStep.objects.create(
            curriculum=self.curriculum,
            step_order=3,
            title="Testing APIs",
            description="API tests",
            estimated_hours=2,
        )
        self.curriculum.status = Curriculum.Status.ACTIVE
        self.curriculum.current_step = self.second_step
        self.curriculum.save(update_fields=["status", "current_step", "updated_at"])
        CurriculumStepProgress.objects.create(
            curriculum=self.curriculum,
            curriculum_step=self.first_step,
            status=CurriculumStepProgress.Status.COMPLETED,
            progress_rate=100,
        )
        CurriculumStepProgress.objects.create(
            curriculum=self.curriculum,
            curriculum_step=self.second_step,
            status=CurriculumStepProgress.Status.IN_PROGRESS,
            progress_rate=0,
        )
        self._login()

        response = self.client.get(self._detail_url(), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["completed_step_count"], 1)
        self.assertEqual(response.data["total_step_count"], 3)
        self.assertEqual(response.data["progress_percent"], 33)
        self.assertEqual(
            response.data["current_step"]["status"],
            CurriculumStepProgress.Status.IN_PROGRESS,
        )
        self.assertEqual(response.data["current_step"]["id"], self.second_step.id)
        self.assertEqual(response.data["current_step"]["order"], self.second_step.step_order)
        self.assertEqual(
            response.data["current_step"]["resources"],
            [],
        )
        self.assertIn(
            third_step.id,
            [step["id"] for step in response.data["steps"]],
        )

    def test_curriculum_detail_maps_curriculum_status_for_api(self):
        self._login()

        response = self.client.get(self._detail_url(), format="json")
        self.assertEqual(response.data["status"], "NOT_STARTED")

        self._start()
        response = self.client.get(self._detail_url(), format="json")
        self.assertEqual(response.data["status"], "IN_PROGRESS")

        self.client.post(self._url("pause"), {}, format="json")
        response = self.client.get(self._detail_url(), format="json")
        self.assertEqual(response.data["status"], "PAUSED")

        self.client.post(self._url("resume"), {}, format="json")
        self.client.post(self._url("complete"), {}, format="json")
        self.client.post(self._url("complete"), {}, format="json")
        response = self.client.get(self._detail_url(), format="json")
        self.assertEqual(response.data["status"], "COMPLETED")

    def test_other_users_curriculum_returns_404(self):
        other_curriculum = Curriculum.objects.create(
            user=self.other_user,
            title="Other roadmap",
            goal="Other goal",
        )
        self._login()

        response = self.client.post(self._url("start", other_curriculum), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_user_cannot_access_learning_api(self):
        response = self.client.post(self._url("start"), {}, format="json")

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_start_is_atomic_when_progress_creation_fails(self):
        def raise_after_schedule(*args, **kwargs):
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            with patch(
                "apps.curriculum.services.curriculum_learning_service.get_or_create_learning_progress",
                side_effect=raise_after_schedule,
            ):
                start_curriculum_learning(
                    self.curriculum,
                    self.user,
                    scheduled_date=date(2026, 6, 16),
                )

        self.assertEqual(LearningSchedule.objects.count(), 0)
        self.assertEqual(LearningProgress.objects.count(), 0)
        self.assertEqual(CurriculumStepProgress.objects.count(), 0)
