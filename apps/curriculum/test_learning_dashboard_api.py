from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Topic
from apps.curriculum.models import (
    Curriculum,
    CurriculumStep,
    CurriculumStepProgress,
    CurriculumStepResource,
    LearningProgress,
    LearningResource,
    LearningSchedule,
)


User = get_user_model()


class LearningDashboardAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="dashboard@example.com",
            password="password123",
            nickname="dashboard",
            agree_terms=True,
        )
        self.other_user = User.objects.create_user(
            email="dashboard-other@example.com",
            password="password123",
            nickname="other",
            agree_terms=True,
        )
        self.client.force_authenticate(user=self.user)

        self.topic = Topic.objects.create(
            name="Django REST Framework",
            slug="django-rest-framework-dashboard",
            depth=2,
            topic_type=Topic.TopicType.SKILL,
        )
        self.resource = LearningResource.objects.create(
            title="DRF tutorial",
            provider="drf",
            provider_name="Django REST Framework",
            resource_type="document",
            difficulty_level="beginner",
            url="https://www.django-rest-framework.org/",
        )

        self.active_curriculum = Curriculum.objects.create(
            user=self.user,
            title="Active roadmap",
            goal="Learn APIs",
            status=Curriculum.Status.ACTIVE,
            target_weeks=4,
            weekly_available_hours=8,
        )
        self.active_first_step = CurriculumStep.objects.create(
            curriculum=self.active_curriculum,
            step_order=1,
            title="Models",
            description="Learn models.",
            estimated_hours=2,
            target_topic=self.topic,
        )
        self.active_second_step = CurriculumStep.objects.create(
            curriculum=self.active_curriculum,
            step_order=2,
            title="Serializers",
            description="Learn serializers.",
            estimated_hours=3,
            target_topic=self.topic,
        )
        self.active_curriculum.current_step = self.active_second_step
        self.active_curriculum.save(update_fields=["current_step", "updated_at"])

        completed_progress = CurriculumStepProgress.objects.create(
            curriculum=self.active_curriculum,
            curriculum_step=self.active_first_step,
            status=CurriculumStepProgress.Status.COMPLETED,
            progress_rate=100,
            completed_at=timezone.now(),
            last_studied_at=timezone.now(),
        )
        active_progress = CurriculumStepProgress.objects.create(
            curriculum=self.active_curriculum,
            curriculum_step=self.active_second_step,
            status=CurriculumStepProgress.Status.IN_PROGRESS,
            progress_rate=20,
            last_studied_at=timezone.now(),
        )
        LearningSchedule.objects.create(
            curriculum_step=self.active_first_step,
            step_progress=completed_progress,
            scheduled_date=timezone.localdate(),
            planned_hours=2,
            status=LearningSchedule.Status.DONE,
        )
        LearningSchedule.objects.create(
            curriculum_step=self.active_second_step,
            step_progress=active_progress,
            scheduled_date=timezone.localdate(),
            planned_hours=1,
            status=LearningSchedule.Status.PLANNED,
        )
        LearningProgress.objects.create(
            curriculum_step=self.active_first_step,
            step_progress=completed_progress,
            status=LearningProgress.Status.COMPLETED,
            actual_minutes=75,
            progress_rate=100,
            studied_at=timezone.localdate(),
            memo="Finished models",
        )
        CurriculumStepResource.objects.create(
            curriculum_step=self.active_second_step,
            learning_resource=self.resource,
            reason="Official docs",
            sort_order=1,
        )

        self.draft_curriculum = Curriculum.objects.create(
            user=self.user,
            title="Draft roadmap",
            goal="Plan later",
            status=Curriculum.Status.DRAFT,
        )
        CurriculumStep.objects.create(
            curriculum=self.draft_curriculum,
            step_order=1,
            title="Draft step",
            description="Draft",
            estimated_hours=1,
        )

        self.completed_curriculum = Curriculum.objects.create(
            user=self.user,
            title="Completed roadmap",
            goal="Already done",
            status=Curriculum.Status.COMPLETED,
        )
        completed_step = CurriculumStep.objects.create(
            curriculum=self.completed_curriculum,
            step_order=1,
            title="Done step",
            description="Done",
            estimated_hours=4,
        )
        CurriculumStepProgress.objects.create(
            curriculum=self.completed_curriculum,
            curriculum_step=completed_step,
            status=CurriculumStepProgress.Status.COMPLETED,
            progress_rate=100,
        )

        self.other_curriculum = Curriculum.objects.create(
            user=self.other_user,
            title="Other roadmap",
            goal="Private",
            status=Curriculum.Status.ACTIVE,
        )
        CurriculumStep.objects.create(
            curriculum=self.other_curriculum,
            step_order=1,
            title="Other step",
            description="Private",
            estimated_hours=10,
        )

    def test_dashboard_returns_user_scoped_summary_current_and_recent_activity(self):
        response = self.client.get("/api/learning/dashboard/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["summary"]["total_curricula"], 3)
        self.assertEqual(response.data["summary"]["active_curricula"], 1)
        self.assertEqual(response.data["summary"]["draft_curricula"], 1)
        self.assertEqual(response.data["summary"]["completed_curricula"], 1)
        self.assertEqual(response.data["summary"]["completed_step_count"], 2)
        self.assertEqual(response.data["summary"]["total_step_count"], 4)
        self.assertEqual(response.data["summary"]["total_estimated_minutes"], 600)
        self.assertEqual(response.data["summary"]["schedule_adherence_percent"], 50)
        self.assertEqual(
            response.data["current_learning"]["curriculum_id"],
            self.active_curriculum.id,
        )
        self.assertEqual(
            response.data["current_learning"]["current_step"]["id"],
            self.active_second_step.id,
        )
        self.assertEqual(len(response.data["recent_activities"]), 1)
        self.assertEqual(response.data["recent_activities"][0]["actual_minutes"], 75)

    def test_dashboard_empty_user_returns_zero_summary_and_null_current(self):
        empty_user = User.objects.create_user(
            email="empty-dashboard@example.com",
            password="password123",
            nickname="empty",
            agree_terms=True,
        )
        self.client.force_authenticate(user=empty_user)

        response = self.client.get("/api/learning/dashboard/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["summary"]["total_curricula"], 0)
        self.assertEqual(response.data["summary"]["schedule_adherence_percent"], None)
        self.assertEqual(response.data["current_learning"], None)
        self.assertEqual(response.data["recent_activities"], [])

    def test_curriculum_progress_returns_sorted_cards_and_status_filter(self):
        response = self.client.get("/api/learning/curriculums/progress/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item["status"] for item in response.data["results"]],
            ["IN_PROGRESS", "NOT_STARTED", "COMPLETED"],
        )
        self.assertEqual(response.data["results"][0]["progress_percent"], 50)
        self.assertEqual(
            response.data["results"][0]["current_step"]["id"],
            self.active_second_step.id,
        )

        filtered = self.client.get(
            "/api/learning/curriculums/progress/",
            {"status": "COMPLETED"},
        )

        self.assertEqual(filtered.status_code, status.HTTP_200_OK)
        self.assertEqual(len(filtered.data["results"]), 1)
        self.assertEqual(filtered.data["results"][0]["id"], self.completed_curriculum.id)

    def test_current_learning_returns_detail_resources_and_schedule(self):
        response = self.client.get("/api/learning/current/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        current = response.data["current"]
        self.assertEqual(current["curriculum"]["id"], self.active_curriculum.id)
        self.assertEqual(current["step"]["id"], self.active_second_step.id)
        self.assertEqual(current["step"]["target_topic"]["name"], "Django REST Framework")
        self.assertEqual(current["resources"][0]["title"], "DRF tutorial")
        self.assertEqual(current["schedule"]["planned_minutes"], 60)
        self.assertEqual(current["next_action"], "CONTINUE")

    def test_current_learning_without_active_or_paused_curriculum_returns_null(self):
        Curriculum.objects.filter(user=self.user).update(status=Curriculum.Status.DRAFT)

        response = self.client.get("/api/learning/current/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["current"], None)

    def test_roadmap_requires_curriculum_id_and_hides_other_users_curriculum(self):
        missing = self.client.get("/api/learning/roadmap/")
        other = self.client.get(
            "/api/learning/roadmap/",
            {"curriculum_id": self.other_curriculum.id},
        )

        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(other.status_code, status.HTTP_404_NOT_FOUND)

    def test_roadmap_returns_ordered_step_timeline(self):
        response = self.client.get(
            "/api/learning/roadmap/",
            {"curriculum_id": self.active_curriculum.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["curriculum"]["id"], self.active_curriculum.id)
        self.assertEqual([step["order"] for step in response.data["steps"]], [1, 2])
        self.assertEqual(response.data["steps"][0]["status"], "COMPLETED")
        self.assertEqual(response.data["steps"][1]["status"], "IN_PROGRESS")
        self.assertEqual(response.data["steps"][1]["estimated_minutes"], 180)
        self.assertEqual(response.data["steps"][1]["resource_count"], 1)

    def test_unauthenticated_requests_are_rejected(self):
        self.client.force_authenticate(user=None)

        response = self.client.get("/api/learning/dashboard/")

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
