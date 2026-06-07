from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Topic, TopicAlias, UserProfile
from apps.curriculum.models import (
    Category,
    CourseTopic,
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
    ResourceTopic,
)


User = get_user_model()


class CurriculumListCreateAPITest(APITestCase):
    """
    커리큘럼 목록 조회와 생성 API의 기본 동작을 검증한다.

    프로필 fallback, 요청 body 우선순위, 잘못된 선호 학습 방식 검증, 사용자별 목록 분리를
    확인한다.
    """

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
    """
    커리큘럼 상세 조회 API의 권한, 중첩 응답, 상태별 진행 데이터 반환 규칙을 검증한다.

    상세 API는 조회 전용이어야 하므로 schedule/progress row 개수가 호출 전후로 변하지 않는지도
    함께 확인한다.
    """

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


class TopicPipelineImportCommandTest(APITestCase):
    """
    topic pipeline CSV import 명령이 공유 가능한 데이터 적재 절차로 동작하는지 검증한다.

    실제 db.sqlite3 파일은 git에 포함되지 않으므로, 팀원들은 migration 후 이 management command로
    CSV 데이터를 각자 import해야 한다. 이 테스트는 명령이 필요한 테이블에 데이터를 넣고, 같은
    CSV를 다시 실행해도 중복 row를 만들지 않는지 확인한다.
    """

    def test_import_topic_pipeline_data_is_idempotent(self):
        with TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            self.write_import_csvs(data_dir)

            call_command("import_topic_pipeline_data", data_dir=str(data_dir))
            call_command("import_topic_pipeline_data", data_dir=str(data_dir))

        self.assertEqual(
            Topic.objects.filter(slug__in=["programming", "python"]).count(),
            2,
        )
        self.assertEqual(TopicAlias.objects.filter(alias_name="파이썬").count(), 1)
        self.assertEqual(
            CurriculumCourse.objects.filter(source_row_number=101).count(),
            1,
        )
        self.assertEqual(LearningResource.objects.filter(lookup_key="resource-1").count(), 1)

        topic = Topic.objects.get(slug="python")
        alias = TopicAlias.objects.get(topic=topic)
        course_topic = CourseTopic.objects.get(topic=topic)
        resource_topic = ResourceTopic.objects.get(topic=topic)

        self.assertEqual(CourseTopic.objects.filter(topic=topic).count(), 1)
        self.assertEqual(ResourceTopic.objects.filter(topic=topic).count(), 1)

        self.assertEqual(alias.alias_name, "파이썬")
        self.assertEqual(course_topic.relevance_score, Decimal("0.90"))
        self.assertTrue(course_topic.is_primary)
        self.assertEqual(resource_topic.learning_resource.lookup_key, "resource-1")

    def write_import_csvs(self, data_dir):
        """
        import command가 요구하는 final CSV 4종을 임시 디렉터리에 생성한다.

        실제 pipeline CSV 전체를 테스트에 넣으면 느리고 취약해지므로, 관계 구조를 검증할 수 있는
        최소 row만 사용한다.
        """
        (data_dir / "final_topics_import.csv").write_text(
            "\n".join(
                [
                    "topic_slug,parent_topic_slug,name,depth,topic_type,is_learning_unit,is_assessable,description,is_active,source",
                    "programming,,프로그래밍,1,domain,false,true,,true,test",
                    "python,programming,Python,2,subject,true,true,,true,test",
                ]
            ),
            encoding="utf-8",
        )
        (data_dir / "final_topic_aliases_import.csv").write_text(
            "\n".join(
                [
                    "topic_lookup_key,alias_name,source,language,alias_type,match_policy,priority,note",
                    "python,파이썬,test,ko,synonym,contains,P0,",
                ]
            ),
            encoding="utf-8",
        )
        (data_dir / "final_course_topics_import.csv").write_text(
            "\n".join(
                [
                    "curriculum_course_lookup_key,course_name,topic_lookup_key,topic_name,topic_depth,parent_topic_slug,relevance_score,extraction_method,is_primary,matched_fields,match_types,link_type",
                    "101,Python 입문,python,Python,2,programming,0.90,keyword,true,course_name,alias,existing_topic",
                ]
            ),
            encoding="utf-8",
        )
        (data_dir / "final_resource_topics_import.csv").write_text(
            "\n".join(
                [
                    "learning_resource_lookup_key,title,topic_lookup_key,topic_name,topic_depth,parent_topic_slug,relevance_score,extraction_method,is_primary,matched_fields,match_types,link_type",
                    "resource-1,Python 공식 문서,python,Python,2,programming,0.80,keyword,true,title,alias,existing_topic",
                ]
            ),
            encoding="utf-8",
        )
