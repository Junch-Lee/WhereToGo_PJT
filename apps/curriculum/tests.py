from datetime import date

from django.contrib.auth import get_user_model
from django.utils import timezone
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
    CurriculumStepProgress,
    CurriculumStepResource,
    LearningProgress,
    LearningResource,
    LearningSchedule,
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


class CurriculumDetailAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="detail@example.com",
            password="testpass123",
            nickname="detail",
            agree_terms=True,
        )
        self.other_user = User.objects.create_user(
            email="detail-other@example.com",
            password="testpass123",
            nickname="detail-other",
            agree_terms=True,
        )
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(name="Backend", slug="backend")
        self.topic = Topic.objects.create(name="Django", slug="django-detail")
        self.resource = LearningResource.objects.create(
            title="DRF 공식 문서",
            description="Django REST Framework 학습 자료",
            url="https://www.django-rest-framework.org/",
            provider="DRF",
            provider_name="DRF",
            resource_type="document",
            difficulty_level="beginner",
        )
        self.course = CurriculumCourse.objects.create(
            course_name="웹 백엔드 실전",
            university_name="Where To Go University",
            department_name="Computer Science",
            grade=3,
            semester="1학기",
            learning_objective="Django 기반 API 서버 구현",
            description="백엔드 프로젝트 강의",
        )
        self.curriculum = Curriculum.objects.create(
            user=self.user,
            title="Django 백엔드 로드맵",
            goal="백엔드 개발자",
            target_weeks=8,
            weekly_available_hours=10,
            preferred_learning_style="project",
        )
        CurriculumCategory.objects.create(
            curriculum=self.curriculum,
            category=self.category,
            is_primary=True,
        )
        self.second_step = CurriculumStep.objects.create(
            curriculum=self.curriculum,
            step_order=2,
            title="DRF 심화",
            description="인증과 권한을 학습한다.",
            target_topic=self.topic,
            difficulty_level="intermediate",
            estimated_hours=12,
        )
        self.first_step = CurriculumStep.objects.create(
            curriculum=self.curriculum,
            step_order=1,
            title="Django 기초",
            description="Django 프로젝트 구조를 학습한다.",
            target_topic=self.topic,
            difficulty_level="beginner",
            estimated_hours=8,
        )
        CurriculumStepResource.objects.create(
            curriculum_step=self.first_step,
            learning_resource=self.resource,
            reason="공식 문서로 기본기를 확인하기 위해 추천한다.",
            sort_order=1,
        )
        CurriculumStepCourse.objects.create(
            curriculum_step=self.first_step,
            curriculum_course=self.course,
            reason="프로젝트 흐름을 익히기 위해 추천한다.",
            sort_order=1,
        )

    def test_get_curriculum_detail_returns_nested_data(self):
        response = self.client.get(f"/api/curriculums/{self.curriculum.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.curriculum.id)
        self.assertEqual(response.data["title"], "Django 백엔드 로드맵")
        self.assertEqual(response.data["preferred_learning_style"], "project")
        self.assertEqual(response.data["categories"][0]["name"], "Backend")
        self.assertTrue(response.data["categories"][0]["is_primary"])
        self.assertEqual(
            [step["step_order"] for step in response.data["steps"]],
            [1, 2],
        )

        first_step = response.data["steps"][0]
        self.assertEqual(first_step["target_topic"]["name"], "Django")
        self.assertEqual(first_step["resources"][0]["title"], "DRF 공식 문서")
        self.assertEqual(first_step["resources"][0]["provider_name"], "DRF")
        self.assertEqual(first_step["resources"][0]["difficulty_level"], "beginner")
        self.assertEqual(first_step["courses"][0]["course_name"], "웹 백엔드 실전")
        self.assertEqual(
            first_step["courses"][0]["university_name"],
            "Where To Go University",
        )
        self.assertEqual(first_step["courses"][0]["department_name"], "Computer Science")
        self.assertEqual(first_step["courses"][0]["grade"], 3)
        self.assertEqual(first_step["courses"][0]["semester"], "1학기")

    def test_draft_curriculum_detail_returns_empty_progress_slots(self):
        response = self.client.get(f"/api/curriculums/{self.curriculum.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Curriculum.Status.DRAFT)
        self.assertEqual(response.data["current_step_id"], None)
        self.assertEqual(response.data["current_step_progress"], None)
        self.assertEqual(response.data["current_step_schedules"], [])
        self.assertEqual(response.data["current_step_learning_progresses"], [])
        self.assertEqual(response.data["steps"][0]["step_progress"], None)

    def test_active_curriculum_detail_returns_current_progress_schedules_and_records(self):
        now = timezone.now()
        self.curriculum.status = Curriculum.Status.ACTIVE
        self.curriculum.current_step = self.first_step
        self.curriculum.started_at = now
        self.curriculum.save(
            update_fields=[
                "status",
                "current_step",
                "started_at",
                "updated_at",
            ],
        )
        step_progress = CurriculumStepProgress.objects.create(
            curriculum=self.curriculum,
            curriculum_step=self.first_step,
            status=CurriculumStepProgress.Status.IN_PROGRESS,
            started_at=now,
            progress_rate=40,
            actual_minutes=120,
            last_studied_at=now,
        )
        schedule = LearningSchedule.objects.create(
            curriculum_step=self.first_step,
            step_progress=step_progress,
            week_no=1,
            sequence_no=1,
            scheduled_date=date(2026, 6, 10),
            planned_hours=2,
            status=LearningSchedule.Status.DONE,
        )
        LearningProgress.objects.create(
            learning_schedule=schedule,
            curriculum_step=self.first_step,
            step_progress=step_progress,
            status=LearningProgress.Status.COMPLETED,
            actual_minutes=120,
            progress_rate=40,
            studied_at=date(2026, 6, 10),
            started_at=now,
            completed_at=now,
            memo="Django 프로젝트 구조 학습",
        )
        other_step_progress = CurriculumStepProgress.objects.create(
            curriculum=self.curriculum,
            curriculum_step=self.second_step,
            status=CurriculumStepProgress.Status.IN_PROGRESS,
            progress_rate=10,
            actual_minutes=30,
        )
        other_schedule = LearningSchedule.objects.create(
            curriculum_step=self.second_step,
            step_progress=other_step_progress,
            week_no=1,
            sequence_no=99,
            scheduled_date=date(2026, 6, 9),
            planned_hours=1,
            status=LearningSchedule.Status.PLANNED,
        )
        LearningProgress.objects.create(
            learning_schedule=other_schedule,
            curriculum_step=self.second_step,
            step_progress=other_step_progress,
            status=LearningProgress.Status.PARTIAL,
            actual_minutes=30,
            progress_rate=10,
            studied_at=date(2026, 6, 9),
            memo="다른 단계 기록",
        )
        schedule_count_before = LearningSchedule.objects.count()
        progress_count_before = LearningProgress.objects.count()

        response = self.client.get(f"/api/curriculums/{self.curriculum.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(LearningSchedule.objects.count(), schedule_count_before)
        self.assertEqual(LearningProgress.objects.count(), progress_count_before)
        self.assertEqual(response.data["current_step_id"], self.first_step.id)
        self.assertEqual(
            response.data["current_step_progress"]["status"],
            CurriculumStepProgress.Status.IN_PROGRESS,
        )
        self.assertEqual(response.data["current_step_progress"]["progress_rate"], 40)
        self.assertEqual(len(response.data["current_step_schedules"]), 1)
        self.assertEqual(response.data["current_step_schedules"][0]["sequence_no"], 1)
        self.assertEqual(
            response.data["current_step_schedules"][0]["status"],
            LearningSchedule.Status.DONE,
        )
        self.assertEqual(len(response.data["current_step_learning_progresses"]), 1)
        self.assertEqual(
            response.data["current_step_learning_progresses"][0]["memo"],
            "Django 프로젝트 구조 학습",
        )
        self.assertEqual(response.data["steps"][0]["step_progress"]["progress_rate"], 40)

    def test_paused_curriculum_detail_returns_only_incomplete_current_schedules(self):
        now = timezone.now()
        self.curriculum.status = Curriculum.Status.PAUSED
        self.curriculum.current_step = self.first_step
        self.curriculum.paused_at = now
        self.curriculum.save(
            update_fields=[
                "status",
                "current_step",
                "paused_at",
                "updated_at",
            ],
        )
        step_progress = CurriculumStepProgress.objects.create(
            curriculum=self.curriculum,
            curriculum_step=self.first_step,
            status=CurriculumStepProgress.Status.PAUSED,
            progress_rate=50,
            actual_minutes=240,
        )
        LearningSchedule.objects.create(
            curriculum_step=self.first_step,
            step_progress=step_progress,
            week_no=1,
            sequence_no=1,
            scheduled_date=date(2026, 6, 10),
            planned_hours=2,
            status=LearningSchedule.Status.DONE,
        )
        LearningSchedule.objects.create(
            curriculum_step=self.first_step,
            step_progress=step_progress,
            week_no=1,
            sequence_no=2,
            scheduled_date=date(2026, 6, 12),
            planned_hours=2,
            status=LearningSchedule.Status.PLANNED,
        )
        LearningSchedule.objects.create(
            curriculum_step=self.first_step,
            step_progress=step_progress,
            week_no=1,
            sequence_no=3,
            scheduled_date=date(2026, 6, 14),
            planned_hours=2,
            status=LearningSchedule.Status.RESCHEDULED,
        )

        response = self.client.get(f"/api/curriculums/{self.curriculum.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["current_step_progress"]["status"],
            CurriculumStepProgress.Status.PAUSED,
        )
        self.assertEqual(
            [item["status"] for item in response.data["current_step_schedules"]],
            [
                LearningSchedule.Status.PLANNED,
                LearningSchedule.Status.RESCHEDULED,
            ],
        )

    def test_get_other_users_curriculum_detail_returns_404(self):
        other_curriculum = Curriculum.objects.create(
            user=self.other_user,
            title="Other roadmap",
            goal="Other goal",
        )

        response = self.client.get(f"/api/curriculums/{other_curriculum.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_missing_curriculum_detail_returns_404(self):
        response = self.client.get("/api/curriculums/999999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_curriculum_detail_returns_401(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(f"/api/curriculums/{self.curriculum.id}/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
