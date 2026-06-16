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
