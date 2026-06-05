from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Topic, UserProfile
from apps.curriculum.models import (
    Category,
    Curriculum,
    CurriculumCourse,
    CurriculumCategory,
    CurriculumStep,
    CurriculumStepCourse,
    CurriculumStepResource,
    LearningResource,
)


User = get_user_model()


class CurriculumListCreateAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="learner@example.com",
            password="testpass123",
            nickname="learner",
            agree_terms=True,
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            nickname="other",
            agree_terms=True,
        )
        self.client.force_authenticate(user=self.user)
        self.url = "/api/curriculums/"

    def test_create_curriculum_uses_profile_fallback_values(self):
        UserProfile.objects.create(
            user=self.user,
            available_weekly_hours=12,
            preferred_learning_style="project",
        )

        response = self.client.post(
            self.url,
            {
                "goal": "Django backend portfolio",
                "target_weeks": 2,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["target_weeks"], 2)
        self.assertEqual(response.data["weekly_available_hours"], 12)
        self.assertEqual(response.data["preferred_learning_style"], "project")
        self.assertEqual(len(response.data["steps"]), 2)
        self.assertTrue(
            Curriculum.objects.filter(
                user=self.user,
                goal="Django backend portfolio",
            ).exists()
        )
        self.assertEqual(CurriculumStep.objects.count(), 2)

    def test_request_values_override_profile_fallback_values(self):
        UserProfile.objects.create(
            user=self.user,
            available_weekly_hours=12,
            preferred_learning_style="project",
        )

        response = self.client.post(
            self.url,
            {
                "goal": "Python data analysis",
                "target_weeks": 1,
                "weekly_available_hours": 5,
                "preferred_learning_style": "theory",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["weekly_available_hours"], 5)
        self.assertEqual(response.data["preferred_learning_style"], "theory")

    def test_create_curriculum_saves_optional_related_rows_when_context_exists(self):
        Category.objects.create(name="Django", slug="django")
        Topic.objects.create(name="Django", slug="django-topic")
        LearningResource.objects.create(
            title="Django REST API guide",
            description="Django backend portfolio resource",
        )
        CurriculumCourse.objects.create(
            course_name="Django backend course",
            learning_objective="Build a Django backend portfolio",
        )

        response = self.client.post(
            self.url,
            {
                "goal": "Django backend portfolio",
                "target_weeks": 2,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CurriculumCategory.objects.count(), 1)
        self.assertEqual(CurriculumStepResource.objects.count(), 2)
        self.assertEqual(CurriculumStepCourse.objects.count(), 2)
        self.assertGreater(
            CurriculumStep.objects.filter(target_topic__isnull=False).count(),
            0,
        )

    def test_invalid_preferred_learning_style_returns_400(self):
        response = self.client.post(
            self.url,
            {
                "goal": "Django backend portfolio",
                "preferred_learning_style": "audio",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("preferred_learning_style", response.data)

    def test_list_only_returns_authenticated_users_curricula(self):
        Curriculum.objects.create(
            user=self.user,
            title="Mine",
            goal="My goal",
        )
        Curriculum.objects.create(
            user=self.other_user,
            title="Other",
            goal="Other goal",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Mine")

    def test_unauthenticated_request_returns_401(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
