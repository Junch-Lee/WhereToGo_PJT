from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Topic, UserInterestTopic, UserProfile


User = get_user_model()


class UserProfileAPITest(APITestCase):
    """
    내 학습 프로필 조회/수정 API를 검증한다.

    관심 토픽, 주간 학습 가능 시간, 선호 학습 방식은 이후 커리큘럼 생성의 fallback 값으로
    쓰이므로 응답 구조와 validation이 유지되는지 확인한다.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="learner@example.com",
            password="testpass123",
            nickname="learner",
            agree_terms=True,
        )
        self.client.force_authenticate(user=self.user)
        self.url = "/api/users/me/profile/"

    def test_get_profile_includes_preferred_learning_style(self):
        topic = Topic.objects.create(name="Backend")
        UserProfile.objects.create(
            user=self.user,
            available_weekly_hours=10,
            preferred_learning_style="project",
        )
        UserInterestTopic.objects.create(user=self.user, topic=topic)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["available_weekly_hours"], 10)
        self.assertEqual(response.data["preferred_learning_style"], "project")
        self.assertEqual(response.data["interest_topics"][0]["name"], "Backend")

    def test_patch_profile_updates_preferred_learning_style(self):
        topic = Topic.objects.create(name="Backend")
        UserProfile.objects.create(
            user=self.user,
            available_weekly_hours=8,
        )
        UserInterestTopic.objects.create(user=self.user, topic=topic)

        response = self.client.patch(
            self.url,
            {"preferred_learning_style": "practice"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["available_weekly_hours"], 8)
        self.assertEqual(response.data["preferred_learning_style"], "practice")
        self.assertEqual(response.data["interest_topics"][0]["name"], "Backend")

    def test_patch_profile_rejects_invalid_preferred_learning_style(self):
        response = self.client.patch(
            self.url,
            {"preferred_learning_style": "audio"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("preferred_learning_style", response.data)
