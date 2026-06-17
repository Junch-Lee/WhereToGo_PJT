from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

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
from apps.curriculum.serializers import CurriculumGenerateSerializer
from apps.curriculum.services.agent_response_service import normalize_agent_response
from apps.curriculum.services.curriculum_save_service import save_ai_generated_curriculum
from apps.curriculum.services.topic_catalog_service import build_topic_catalog


User = get_user_model()


class AgentResponseServiceTest(APITestCase):
    """AI Agent 내부 결과를 백엔드 계약 schema로 바꾸는 순수 service를 검증한다."""

    def test_generated_status_is_normalized_to_success(self):
        result = normalize_agent_response(
            {
                "generation_status": "generated",
                "user_profile": {
                    "goal": "Python",
                    "target_weeks": 8,
                },
                "curriculum": {
                    "title": "Python roadmap",
                    "recommendation_reason": "Matched Python resources.",
                    "steps": [
                        {
                            "step_order": 1,
                            "title": "Python basics",
                            "description": "Learn syntax.",
                            "target_topic_slug": "python",
                            "difficulty_level": "beginner",
                            "estimated_hours": 5,
                            "prerequisite_note": "",
                            "course_source_row_numbers": [10164],
                            "resource_external_ids": ["resource-1"],
                        }
                    ],
                },
            }
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["title"], "Python roadmap")
        self.assertEqual(result["steps"][0]["order"], 1)
        self.assertEqual(result["steps"][0]["target_topic_slug"], "python")
        self.assertEqual(result["steps"][0]["course_source_row_numbers"], [10164])
        self.assertEqual(result["steps"][0]["resource_external_ids"], ["resource-1"])

    def test_insufficient_search_results_status_is_normalized_to_no_results(self):
        result = normalize_agent_response(
            {
                "generation_status": "insufficient_search_results",
                "message": "검색 결과가 부족합니다.",
            }
        )

        self.assertEqual(result["status"], "no_results")
        self.assertEqual(result["message"], "검색 결과가 부족합니다.")

    def test_out_of_scope_status_is_preserved(self):
        result = normalize_agent_response(
            {
                "generation_status": "out_of_scope",
                "message": "컴퓨터공학 분야만 지원합니다.",
                "topic_analysis": {
                    "needs_clarification": True,
                    "clarification_question": "컴퓨터공학 목표를 입력해 주세요.",
                },
            }
        )

        self.assertEqual(result["status"], "out_of_scope")
        self.assertEqual(result["message"], "컴퓨터공학 분야만 지원합니다.")

    def test_needs_clarification_is_detected_from_topic_analysis(self):
        result = normalize_agent_response(
            {
                "topic_analysis": {
                    "needs_clarification": True,
                    "clarification_question": "어떤 주제를 배우고 싶나요?",
                },
            }
        )

        self.assertEqual(result["status"], "needs_clarification")
        self.assertEqual(result["clarification_question"], "어떤 주제를 배우고 싶나요?")

    def test_unknown_generation_status_raises_value_error(self):
        with self.assertRaises(ValueError):
            normalize_agent_response({"generation_status": "unexpected"})


class TopicCatalogServiceTest(APITestCase):
    """Topic/TopicAlias ORM 데이터를 AI Agent catalog dict로 변환하는 service를 검증한다."""

    def test_build_topic_catalog_returns_active_topics_with_parent_and_aliases(self):
        parent = Topic.objects.create(
            name="Catalog Test Parent",
            slug="catalog-test-parent",
            depth=1,
            topic_type=Topic.TopicType.DOMAIN,
            is_learning_unit=False,
            is_assessable=False,
            is_active=True,
        )
        child = Topic.objects.create(
            name="Catalog Test Child",
            slug="catalog-test-child",
            parent_topic=parent,
            depth=2,
            topic_type=Topic.TopicType.SUBJECT,
            is_learning_unit=True,
            is_assessable=True,
            is_active=True,
        )
        Topic.objects.create(
            name="Inactive",
            slug="inactive-topic",
            depth=2,
            topic_type=Topic.TopicType.SUBJECT,
            is_active=False,
        )
        TopicAlias.objects.create(
            topic=child,
            alias_name="파이썬",
            match_policy="contains",
        )
        TopicAlias.objects.create(
            topic=child,
            alias_name="Python Programming",
            match_policy="normalized_exact",
        )

        catalog = build_topic_catalog()
        by_slug = {item["slug"]: item for item in catalog}

        self.assertIn("catalog-test-parent", by_slug)
        self.assertIn("catalog-test-child", by_slug)
        self.assertNotIn("inactive-topic", by_slug)
        self.assertEqual(by_slug["catalog-test-child"]["parent_slug"], "catalog-test-parent")
        self.assertCountEqual(
            by_slug["catalog-test-child"]["aliases"],
            ["파이썬", "Python Programming"],
        )
        self.assertIsInstance(by_slug["catalog-test-child"]["aliases"], list)
        self.assertIsNone(by_slug["catalog-test-parent"]["parent_slug"])

        required_keys = {
            "id",
            "slug",
            "name",
            "parent_slug",
            "depth",
            "topic_type",
            "is_learning_unit",
            "is_assessable",
            "aliases",
        }
        self.assertEqual(set(by_slug["catalog-test-child"].keys()), required_keys)


class AICurriculumSaveServiceTest(APITestCase):
    """normalized AI 결과를 identifier 기반으로 저장하는 service를 검증한다."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="ai-save@example.com",
            password="testpass123",
            nickname="ai-save",
            agree_terms=True,
        )
        self.topic = Topic.objects.create(
            name="Python",
            slug="python-ai-save",
            depth=2,
            topic_type=Topic.TopicType.SUBJECT,
            is_active=True,
        )
        self.fallback_topic = Topic.objects.create(
            name="Computer Science Basics",
            slug="computer-science-basics",
            depth=1,
            topic_type=Topic.TopicType.DOMAIN,
            is_active=True,
        )
        self.course = CurriculumCourse.objects.create(
            course_name="Python Course",
            source_row_number=10164,
        )
        self.resource = LearningResource.objects.create(
            title="Python Resource",
            lookup_key="resource-10164",
        )

    def test_save_success_ai_result_creates_curriculum_steps_and_links(self):
        """normalized success 결과가 Curriculum/Step/Course/Resource로 저장되는지 검증한다."""
        curriculum = save_ai_generated_curriculum(self.user, self._ai_result())

        self.assertEqual(curriculum.user, self.user)
        self.assertEqual(curriculum.title, "Python roadmap")
        self.assertEqual(curriculum.goal, "Learn Python")
        self.assertEqual(curriculum.target_weeks, 8)
        self.assertEqual(curriculum.weekly_available_hours, 10)
        self.assertEqual(curriculum.difficulty_level, "beginner")
        self.assertEqual(curriculum.preferred_learning_style, "project")

        step = CurriculumStep.objects.get(curriculum=curriculum)
        self.assertEqual(step.step_order, 1)
        self.assertEqual(step.target_topic, self.topic)

        step_course = CurriculumStepCourse.objects.get(curriculum_step=step)
        self.assertEqual(step_course.curriculum_course, self.course)

        step_resource = CurriculumStepResource.objects.get(curriculum_step=step)
        self.assertEqual(step_resource.learning_resource, self.resource)

    def test_save_success_ai_result_accepts_weekly_available_hours_key(self):
        """AI가 새 user_profile key로 반환한 주간 학습 시간을 그대로 저장하는지 검증한다.

        실제 Generate API의 ``to_raw_input()``과 최신 AI user_profile은 백엔드 필드명인
        ``weekly_available_hours``를 사용한다. 저장 service가 과거 key인 ``weekly_hours``만
        읽으면 사용자가 10시간을 선택해도 기본값 7시간으로 저장되는 통합 버그가 생기므로,
        새 key를 우선 처리하는 계약을 테스트로 고정한다.
        """
        ai_result = self._ai_result()
        ai_result["user_profile"].pop("weekly_hours")
        ai_result["user_profile"]["weekly_available_hours"] = 10

        curriculum = save_ai_generated_curriculum(self.user, ai_result)

        self.assertEqual(curriculum.weekly_available_hours, 10)

    def test_missing_identifier_targets_are_skipped_or_saved_as_null_topic(self):
        """존재하지 않는 AI identifier가 있어도 저장 흐름이 중단되지 않는지 검증한다.

        AI가 반환한 topic/course/resource 식별자는 검색 index와 DB 동기화 상태에 따라
        일부 누락될 수 있다. 이 경우 500으로 실패하면 사용 가능한 나머지 추천까지 잃게
        되므로, 누락 FK는 skip하거나 null topic으로 저장하는 방어 정책을 확인한다.
        """
        ai_result = self._ai_result(
            target_topic_slug="missing-topic",
            course_source_row_numbers=[10164, 999999],
            resource_external_ids=["resource-10164", "missing-resource"],
        )

        curriculum = save_ai_generated_curriculum(self.user, ai_result)
        step = CurriculumStep.objects.get(curriculum=curriculum)

        # target_topic은 필수 FK가 아니므로, slug를 못 찾으면 단계 자체는 남기고 null로 둔다.
        self.assertIsNone(step.target_topic)
        # 존재하는 course/resource는 연결하고, 존재하지 않는 identifier만 skip한다.
        # 이렇게 해야 부분 누락 데이터가 전체 커리큘럼 저장 실패로 번지지 않는다.
        self.assertEqual(CurriculumStepCourse.objects.filter(curriculum_step=step).count(), 1)
        self.assertEqual(CurriculumStepResource.objects.filter(curriculum_step=step).count(), 1)

    def test_computer_science_slug_uses_backend_fallback_mapping(self):
        """AI의 넓은 computer-science slug가 저장 시 기본 토픽으로 fallback되는지 검증한다.

        AI 분석 결과가 상위 개념인 ``computer-science``를 반환해도 현재 DB에는 저장 가능한
        학습 단위로 ``computer-science-basics``가 준비될 수 있다. 이 테스트는 그 통합
        보정 규칙이 깨지지 않도록 고정한다.
        """
        curriculum = save_ai_generated_curriculum(
            self.user,
            self._ai_result(target_topic_slug="computer-science"),
        )

        step = CurriculumStep.objects.get(curriculum=curriculum)
        self.assertEqual(step.target_topic, self.fallback_topic)

    def test_duplicate_course_and_resource_identifiers_are_linked_once(self):
        curriculum = save_ai_generated_curriculum(
            self.user,
            self._ai_result(
                course_source_row_numbers=[10164, 10164],
                resource_external_ids=["resource-10164", "resource-10164"],
            ),
        )
        step = CurriculumStep.objects.get(curriculum=curriculum)

        self.assertEqual(CurriculumStepCourse.objects.filter(curriculum_step=step).count(), 1)
        self.assertEqual(CurriculumStepResource.objects.filter(curriculum_step=step).count(), 1)

    def test_non_success_status_does_not_save_curriculum(self):
        with self.assertRaises(ValueError):
            save_ai_generated_curriculum(
                self.user,
                {
                    "status": "no_results",
                    "message": "검색 결과가 부족합니다.",
                },
            )

        self.assertEqual(Curriculum.objects.count(), 0)

    def test_transaction_rolls_back_when_unexpected_error_occurs(self):
        with self.assertRaises(Exception):
            save_ai_generated_curriculum(
                self.user,
                self._ai_result(
                    steps=[
                        {
                            "order": 1,
                            "title": "First",
                            "description": "First step",
                            "target_topic_slug": "python-ai-save",
                        },
                        {
                            "order": 1,
                            "title": "Duplicate",
                            "description": "Duplicate order",
                            "target_topic_slug": "python-ai-save",
                        },
                    ],
                ),
            )

        self.assertEqual(Curriculum.objects.count(), 0)
        self.assertEqual(CurriculumStep.objects.count(), 0)

    def _ai_result(
        self,
        target_topic_slug="python-ai-save",
        course_source_row_numbers=None,
        resource_external_ids=None,
        steps=None,
    ):
        return {
            "status": "success",
            "title": "Python roadmap",
            "recommendation_reason": "Python 학습 목표에 맞춘 추천입니다.",
            "user_profile": {
                "goal": "Learn Python",
                "target_weeks": 8,
                "weekly_hours": 10,
                "difficulty_level": "beginner",
                "preferred_learning_style": "project",
            },
            "steps": steps
            if steps is not None
            else [
                {
                    "order": 1,
                    "title": "Python basics",
                    "description": "Learn Python syntax.",
                    "target_topic_slug": target_topic_slug,
                    "difficulty_level": "beginner",
                    "estimated_hours": 10,
                    "prerequisite_note": "",
                    "course_source_row_numbers": course_source_row_numbers
                    if course_source_row_numbers is not None
                    else [10164],
                    "resource_external_ids": resource_external_ids
                    if resource_external_ids is not None
                    else ["resource-10164"],
                }
            ],
        }


class CurriculumGenerateSerializerTest(APITestCase):
    """Generate API 입력 serializer가 MVP 질문 계약과 AI raw_input 계약을 잇는지 검증한다."""

    def test_to_raw_input_maps_mvp_questions_to_agent_schema(self):
        """MVP 6개 질문 payload가 AI Agent 입력 key로 정확히 변환되는지 검증한다.

        View가 ``request.data``를 직접 AI에 넘기면 검증되지 않은 값이나 프론트 전용
        필드명이 섞일 수 있다. 이 테스트는 serializer가 백엔드/API 필드명을 AI 분석
        노드가 기대하는 ``goal_text``, ``level`` 같은 key로 바꾸는 통합 지점을 고정한다.
        Q7 ``concern``은 MVP에서 제외되었지만, 현재 AI 입력 호환을 위해 빈 문자열을
        넣는 정책까지 함께 검증한다.
        """
        serializer = CurriculumGenerateSerializer(data=self._mvp_payload())

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.to_raw_input(),
            {
                "goal_text": "백엔드 개발",
                "purpose": "portfolio",
                "level": "beginner",
                "period": 8,
                "weekly_hours": 10,
                "learning_style": "project",
                "concern": "",
            },
        )

    def test_concern_is_not_required_for_mvp_generate_request(self):
        """MVP에서 제외된 Q7 concern 없이도 serializer 검증이 통과하는지 확인한다.

        이 검증은 프론트가 최종 6개 질문만 보내는 현재 API 계약을 보호한다. AI 쪽
        호환용 ``concern`` 빈 값은 ``to_raw_input()`` 내부에서만 만들어지며, 사용자에게
        입력 필드로 요구하지 않는다.
        """
        payload = self._mvp_payload()
        payload.pop("preferred_learning_style")
        payload["preferred_learning_style"] = "balanced"

        serializer = CurriculumGenerateSerializer(data=payload)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("concern", serializer.validated_data)
        self.assertEqual(serializer.to_raw_input()["concern"], "")

    def test_required_mvp_fields_are_validated(self):
        """필수 MVP 질문 누락 시 serializer가 validation error를 반환하는지 검증한다.

        Generate API는 6개 질문을 모두 받은 뒤 AI graph를 실행해야 한다. 필수 입력이
        빠진 상태로 AI를 호출하면 분석 노드의 fallback에 의존하게 되어 통합 오류를
        늦게 발견하므로 serializer 단계에서 막는다.
        """
        for field_name in ["goal", "target_weeks", "weekly_available_hours"]:
            payload = self._mvp_payload()
            payload.pop(field_name)

            serializer = CurriculumGenerateSerializer(data=payload)

            self.assertFalse(serializer.is_valid(), field_name)
            self.assertIn(field_name, serializer.errors)

    def test_choice_fields_reject_unknown_values(self):
        """프론트 분기형 질문의 허용되지 않은 내부 값이 거부되는지 검증한다.

        purpose, 난이도, 기간, 주간 시간, 학습 방식은 추천 품질과 저장 값에 직접 영향을
        준다. 따라서 UI label이나 임의 문자열이 들어와도 AI 호출 전에 명확히 실패해야 한다.
        """
        invalid_cases = {
            "purpose": "취업",
            "difficulty_level": "expert",
            "target_weeks": 16,
            "weekly_available_hours": 15,
            "preferred_learning_style": "video",
        }

        for field_name, invalid_value in invalid_cases.items():
            payload = self._mvp_payload(**{field_name: invalid_value})
            serializer = CurriculumGenerateSerializer(data=payload)

            self.assertFalse(serializer.is_valid(), field_name)
            self.assertIn(field_name, serializer.errors)

    def _mvp_payload(
        self,
        goal="백엔드 개발",
        purpose="portfolio",
        difficulty_level="beginner",
        target_weeks=8,
        weekly_available_hours=10,
        preferred_learning_style="project",
    ):
        """Serializer 테스트에서 사용하는 표준 MVP 6개 질문 payload를 만든다."""
        return {
            "goal": goal,
            "purpose": purpose,
            "difficulty_level": difficulty_level,
            "target_weeks": target_weeks,
            "weekly_available_hours": weekly_available_hours,
            "preferred_learning_style": preferred_learning_style,
        }


class CurriculumGenerateAPITest(APITestCase):
    """AI 커리큘럼 생성 API가 MVP 6개 입력을 검증하고 orchestration만 담당하는지 검증한다."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="ai-generate@example.com",
            password="testpass123",
            nickname="ai-generate",
            agree_terms=True,
        )
        self.client.force_authenticate(user=self.user)
        self.url = "/api/curriculums/generate/"

    @patch("apps.curriculum.views.save_ai_generated_curriculum")
    @patch("apps.curriculum.views.normalize_agent_response")
    @patch("apps.curriculum.views.run_agent")
    @patch("apps.curriculum.views.build_topic_catalog")
    def test_generate_curriculum_success_returns_preview_without_saving(
        self,
        build_topic_catalog_mock,
        run_agent_mock,
        normalize_agent_response_mock,
        save_ai_generated_curriculum_mock,
    ):
        """success 흐름에서 View가 저장 없이 미리보기 결과를 반환하는지 검증한다.

        실제 ``run_agent``는 OpenAI, vector search 같은 외부 의존성을 가질 수 있으므로
        mock 처리한다. 이 테스트의 목적은 AI 품질이나 저장 service 내부 로직이 아니라,
        Generate API가 검증된 raw_input과 topic catalog를 AI에 넘기고, 정규화된 success
        결과를 결과 페이지용 미리보기 데이터로 반환하는 orchestration 경계 검증이다.
        """
        catalog = [{"slug": "python", "name": "Python"}]
        agent_result = {"generation_status": "generated"}
        normalized_result = self._normalized_success_result()
        # build_topic_catalog는 PR1에서 별도 검증했으므로 여기서는 반환 catalog를 고정한다.
        # 그래야 View가 catalog를 만든 뒤 run_agent의 두 번째 인자로 넘기는지만 확인할 수 있다.
        build_topic_catalog_mock.return_value = catalog
        # run_agent는 외부 AI/검색 의존성을 실행하지 않도록 mock한다.
        # PR4 통합 테스트는 실제 AI 호출 없이 API wiring만 검증해야 CI에서 안정적이다.
        run_agent_mock.return_value = agent_result
        # normalize_agent_response는 PR1 service 테스트가 담당한다.
        # 여기서는 View가 AI 내부 결과를 정규화 service에 넘기는지만 확인한다.
        normalize_agent_response_mock.return_value = normalized_result
        # Generate API는 이제 저장하지 않고 결과 페이지에서 사용할 미리보기 payload만 반환한다.

        response = self.client.post(
            self.url,
            self._mvp_payload(goal="Python 배우기"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["generated_curriculum"], normalized_result)
        build_topic_catalog_mock.assert_called_once_with()
        run_agent_mock.assert_called_once_with(
            {
                "goal_text": "Python 배우기",
                "purpose": "portfolio",
                "level": "beginner",
                "period": 8,
                "weekly_hours": 10,
                "learning_style": "project",
                "concern": "",
            },
            catalog,
        )
        normalize_agent_response_mock.assert_called_once_with(agent_result)
        save_ai_generated_curriculum_mock.assert_not_called()

    @patch("apps.curriculum.views.save_ai_generated_curriculum")
    @patch("apps.curriculum.views.normalize_agent_response")
    @patch("apps.curriculum.views.run_agent")
    @patch("apps.curriculum.views.build_topic_catalog")
    def test_generate_curriculum_maps_mvp_payload_to_ai_raw_input(
        self,
        build_topic_catalog_mock,
        run_agent_mock,
        normalize_agent_response_mock,
        save_ai_generated_curriculum_mock,
    ):
        """MVP 6개 질문 payload가 Generate API를 통과해 AI raw_input으로 변환되는지 검증한다.

        serializer 단독 테스트와 별개로, 실제 API 호출 경로에서도 ``to_raw_input()`` 결과가
        ``run_agent``에 들어가는지 확인한다. 이중 검증을 두는 이유는 View가 실수로
        ``request.data``나 ``validated_data``를 직접 넘기도록 바뀌는 회귀를 잡기 위해서다.
        """
        build_topic_catalog_mock.return_value = []
        run_agent_mock.return_value = {"generation_status": "generated"}
        normalize_agent_response_mock.return_value = self._normalized_success_result()

        response = self.client.post(
            self.url,
            self._mvp_payload(
                goal="Django 배우기",
                purpose="job",
                difficulty_level="intermediate",
                target_weeks=12,
                weekly_available_hours=20,
                preferred_learning_style="balanced",
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        raw_input = run_agent_mock.call_args.args[0]
        self.assertEqual(raw_input["goal_text"], "Django 배우기")
        self.assertEqual(raw_input["purpose"], "job")
        self.assertEqual(raw_input["period"], 12)
        self.assertEqual(raw_input["weekly_hours"], 20)
        self.assertEqual(raw_input["level"], "intermediate")
        self.assertEqual(raw_input["learning_style"], "balanced")
        self.assertEqual(raw_input["concern"], "")
        save_ai_generated_curriculum_mock.assert_not_called()

    @patch("apps.curriculum.views.normalize_agent_response")
    @patch("apps.curriculum.views.run_agent")
    @patch("apps.curriculum.views.build_topic_catalog")
    def test_generate_curriculum_preview_uses_requested_target_weeks(
        self,
        build_topic_catalog_mock,
        run_agent_mock,
        normalize_agent_response_mock,
    ):
        """1/2/3/6개월 선택값이 AI 기본값에 덮이지 않고 미리보기 기간에 반영되는지 검증한다."""
        build_topic_catalog_mock.return_value = []
        run_agent_mock.return_value = {"generation_status": "generated"}

        for target_weeks in [4, 8, 12, 24]:
            with self.subTest(target_weeks=target_weeks):
                ai_result = self._normalized_success_result()
                ai_result["user_profile"]["target_weeks"] = 8
                normalize_agent_response_mock.return_value = ai_result

                response = self.client.post(
                    self.url,
                    self._mvp_payload(target_weeks=target_weeks),
                    format="json",
                )

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(
                    response.data["generated_curriculum"]["user_profile"]["target_weeks"],
                    target_weeks,
                )

    @patch("apps.curriculum.views.normalize_agent_response")
    @patch("apps.curriculum.views.run_agent")
    @patch("apps.curriculum.views.build_topic_catalog")
    def test_generate_curriculum_preview_includes_reference_names(
        self,
        build_topic_catalog_mock,
        run_agent_mock,
        normalize_agent_response_mock,
    ):
        """AI identifier에 매칭되는 자료/강의 이름을 결과 페이지 미리보기에 붙인다."""
        LearningResource.objects.create(
            lookup_key="resource-python-docs",
            title="Python 공식 문서",
            resource_type="document",
            provider_name="Python",
        )
        CurriculumCourse.objects.create(
            source_row_number=10164,
            course_name="Python 프로그래밍 입문",
            university_name="Where To Go University",
        )
        ai_result = self._normalized_success_result()
        ai_result["steps"] = [
            {
                "order": 1,
                "title": "Python 기초",
                "description": "Python 문법을 학습합니다.",
                "target_topic_slug": "python",
                "difficulty_level": "beginner",
                "estimated_hours": 8,
                "prerequisite_note": "",
                "course_source_row_numbers": [10164],
                "resource_external_ids": ["resource-python-docs"],
            }
        ]
        build_topic_catalog_mock.return_value = []
        run_agent_mock.return_value = {"generation_status": "generated"}
        normalize_agent_response_mock.return_value = ai_result

        response = self.client.post(
            self.url,
            self._mvp_payload(),
            format="json",
        )

        step = response.data["generated_curriculum"]["steps"][0]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(step["preview_resources"][0]["title"], "Python 공식 문서")
        self.assertEqual(step["preview_courses"][0]["course_name"], "Python 프로그래밍 입문")

    @patch("apps.curriculum.views.save_ai_generated_curriculum")
    @patch("apps.curriculum.views.normalize_agent_response")
    @patch("apps.curriculum.views.run_agent")
    @patch("apps.curriculum.views.build_topic_catalog")
    def test_generate_curriculum_out_of_scope_does_not_save(
        self,
        build_topic_catalog_mock,
        run_agent_mock,
        normalize_agent_response_mock,
        save_ai_generated_curriculum_mock,
    ):
        """out_of_scope 상태에서는 저장하지 않고 안내 응답만 반환하는지 검증한다.

        AI가 지원 범위 밖이라고 판단한 결과는 사용자의 커리큘럼 목록에 남기면 안 된다.
        그래서 저장 service가 호출되지 않는지를 명시적으로 확인한다.
        """
        build_topic_catalog_mock.return_value = []
        run_agent_mock.return_value = {"generation_status": "out_of_scope"}
        normalize_agent_response_mock.return_value = {
            "status": "out_of_scope",
            "message": "컴퓨터공학 학습 목표만 지원합니다.",
        }

        response = self.client.post(
            self.url,
            self._mvp_payload(goal="요리 배우기"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "out_of_scope")
        save_ai_generated_curriculum_mock.assert_not_called()

    @patch("apps.curriculum.views.save_ai_generated_curriculum")
    @patch("apps.curriculum.views.normalize_agent_response")
    @patch("apps.curriculum.views.run_agent")
    @patch("apps.curriculum.views.build_topic_catalog")
    def test_generate_curriculum_needs_clarification_does_not_save(
        self,
        build_topic_catalog_mock,
        run_agent_mock,
        normalize_agent_response_mock,
        save_ai_generated_curriculum_mock,
    ):
        """needs_clarification 상태에서는 추가 질문을 반환하고 저장하지 않는지 검증한다.

        이 상태는 아직 생성 가능한 커리큘럼이 아니라 사용자 입력을 더 받아야 하는 중간
        상태다. 빈 Curriculum row가 생성되지 않도록 저장 service 미호출을 확인한다.
        """
        build_topic_catalog_mock.return_value = []
        run_agent_mock.return_value = {"topic_analysis": {"needs_clarification": True}}
        normalize_agent_response_mock.return_value = {
            "status": "needs_clarification",
            "clarification_question": "어떤 개발 분야를 배우고 싶나요?",
        }

        response = self.client.post(
            self.url,
            self._mvp_payload(goal="개발 배우기"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "needs_clarification")
        self.assertEqual(response.data["clarification_question"], "어떤 개발 분야를 배우고 싶나요?")
        save_ai_generated_curriculum_mock.assert_not_called()

    @patch("apps.curriculum.views.save_ai_generated_curriculum")
    @patch("apps.curriculum.views.normalize_agent_response")
    @patch("apps.curriculum.views.run_agent")
    @patch("apps.curriculum.views.build_topic_catalog")
    def test_generate_curriculum_no_results_does_not_save(
        self,
        build_topic_catalog_mock,
        run_agent_mock,
        normalize_agent_response_mock,
        save_ai_generated_curriculum_mock,
    ):
        """no_results 상태에서는 저장하지 않고 검색 부족 안내를 반환하는지 검증한다.

        검색 결과가 부족한 경우에는 추천 근거가 불완전하므로 Curriculum/Step을 저장하지
        않아야 한다. 이 테스트는 실패성 응답이 사용자 데이터로 남지 않는 정책을 고정한다.
        """
        build_topic_catalog_mock.return_value = []
        run_agent_mock.return_value = {"generation_status": "insufficient_search_results"}
        normalize_agent_response_mock.return_value = {
            "status": "no_results",
            "message": "검색 결과가 부족합니다.",
        }

        response = self.client.post(
            self.url,
            self._mvp_payload(goal="희귀한 주제 배우기"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "no_results")
        save_ai_generated_curriculum_mock.assert_not_called()

    @patch("apps.curriculum.views.logger")
    @patch("apps.curriculum.views.save_ai_generated_curriculum")
    @patch("apps.curriculum.views.normalize_agent_response")
    @patch("apps.curriculum.views.run_agent")
    @patch("apps.curriculum.views.build_topic_catalog")
    def test_generate_curriculum_agent_error_returns_502(
        self,
        build_topic_catalog_mock,
        run_agent_mock,
        normalize_agent_response_mock,
        save_ai_generated_curriculum_mock,
        logger_mock,
    ):
        """run_agent 예외가 raw exception 노출 없이 안전한 오류 응답으로 바뀌는지 검증한다.

        외부 AI 호출은 네트워크, 모델, vector search 실패 가능성이 있다. API는 내부 예외
        문구를 사용자에게 그대로 노출하지 않고, 저장도 수행하지 않아야 한다.
        """
        build_topic_catalog_mock.return_value = []
        run_agent_mock.side_effect = RuntimeError("agent failed")

        response = self.client.post(
            self.url,
            self._mvp_payload(goal="Python 배우기"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(response.data["status"], "error")
        self.assertNotIn("agent failed", response.data["message"])
        logger_mock.exception.assert_called_once_with("AI curriculum generation failed.")
        normalize_agent_response_mock.assert_not_called()
        save_ai_generated_curriculum_mock.assert_not_called()

    @patch("apps.curriculum.views.normalize_agent_response")
    @patch("apps.curriculum.views.run_agent")
    @patch("apps.curriculum.views.build_topic_catalog")
    def test_generate_curriculum_stream_returns_progress_and_done_events(
        self,
        build_topic_catalog_mock,
        run_agent_mock,
        normalize_agent_response_mock,
    ):
        build_topic_catalog_mock.return_value = [{"slug": "python", "name": "Python"}]
        run_agent_mock.return_value = {"generation_status": "generated"}
        normalize_agent_response_mock.return_value = self._normalized_success_result()

        response = self.client.post(
            "/api/curriculums/generate/stream/",
            self._mvp_payload(goal="Python 배우기"),
            format="json",
        )
        stream_body = b"".join(response.streaming_content).decode("utf-8")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response["Content-Type"].startswith("text/event-stream"))
        self.assertIn("event: progress", stream_body)
        self.assertIn("event: done", stream_body)
        self.assertIn('"status": "success"', stream_body)
        self.assertIn('"generated_curriculum"', stream_body)
        run_agent_mock.assert_called_once()

    def test_generate_curriculum_stream_returns_error_event_for_invalid_payload(self):
        response = self.client.post(
            "/api/curriculums/generate/stream/",
            {
                "purpose": "portfolio",
                "difficulty_level": "beginner",
                "target_weeks": 8,
                "weekly_available_hours": 10,
                "preferred_learning_style": "project",
            },
            format="json",
        )
        stream_body = b"".join(response.streaming_content).decode("utf-8")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("event: error", stream_body)
        self.assertIn('"detail"', stream_body)
        self.assertIn('"goal"', stream_body)

    def test_generate_curriculum_requires_goal(self):
        """학습 목표가 빠진 요청은 AI 호출 전에 400으로 거부되는지 검증한다."""
        response = self.client.post(
            self.url,
            {
                "purpose": "portfolio",
                "difficulty_level": "beginner",
                "target_weeks": 8,
                "weekly_available_hours": 10,
                "preferred_learning_style": "project",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("goal", response.data)

    def test_generate_curriculum_rejects_invalid_purpose(self):
        """허용되지 않은 purpose 값이 serializer validation error를 발생시키는지 검증한다."""
        response = self.client.post(
            self.url,
            self._mvp_payload(purpose="취업"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("purpose", response.data)

    def test_generate_curriculum_rejects_invalid_difficulty_level(self):
        """허용되지 않은 difficulty_level 값이 serializer validation error를 발생시키는지 검증한다."""
        response = self.client.post(
            self.url,
            self._mvp_payload(difficulty_level="expert"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("difficulty_level", response.data)

    def test_generate_curriculum_rejects_invalid_target_weeks(self):
        """허용되지 않은 target_weeks 값이 serializer validation error를 발생시키는지 검증한다."""
        response = self.client.post(
            self.url,
            self._mvp_payload(target_weeks=16),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("target_weeks", response.data)

    def test_generate_curriculum_rejects_invalid_weekly_available_hours(self):
        """허용되지 않은 weekly_available_hours 값이 validation error를 발생시키는지 검증한다."""
        response = self.client.post(
            self.url,
            self._mvp_payload(weekly_available_hours=15),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("weekly_available_hours", response.data)

    def test_generate_curriculum_rejects_invalid_preferred_learning_style(self):
        """허용되지 않은 preferred_learning_style 값이 validation error를 발생시키는지 검증한다."""
        response = self.client.post(
            self.url,
            self._mvp_payload(preferred_learning_style="video"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("preferred_learning_style", response.data)

    @patch("apps.curriculum.views.save_ai_generated_curriculum")
    def test_save_generated_curriculum_persists_preview_result(
        self,
        save_ai_generated_curriculum_mock,
    ):
        """결과 페이지에서 확정한 미리보기 결과만 저장 service로 전달하는지 검증한다."""
        normalized_result = self._normalized_success_result()
        saved_curriculum = Curriculum.objects.create(
            user=self.user,
            title="Python roadmap",
            goal="Python 배우기",
        )
        save_ai_generated_curriculum_mock.return_value = saved_curriculum

        response = self.client.post(
            "/api/curriculums/save-generated/",
            {"generated_curriculum": normalized_result},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["curriculum_id"], saved_curriculum.id)
        save_ai_generated_curriculum_mock.assert_called_once_with(
            self.user,
            normalized_result,
        )

    def test_save_generated_curriculum_rejects_non_success_preview(self):
        """success가 아닌 생성 결과는 저장 버튼 API에서도 DB에 남기지 않는다."""
        response = self.client.post(
            "/api/curriculums/save-generated/",
            {
                "generated_curriculum": {
                    "status": "no_results",
                    "message": "검색 결과가 부족합니다.",
                }
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Curriculum.objects.count(), 0)

    def _mvp_payload(
        self,
        goal="백엔드 개발",
        purpose="portfolio",
        difficulty_level="beginner",
        target_weeks=8,
        weekly_available_hours=10,
        preferred_learning_style="project",
    ):
        """Generate API 테스트에서 사용하는 MVP 6개 질문 payload를 만든다.

        모든 테스트가 같은 입력 계약을 공유해야 스키마 변경 시 누락을 빨리 발견할 수 있다.
        ``concern``은 MVP 질문에서 제외되었으므로 helper에도 넣지 않는다.
        """
        return {
            "goal": goal,
            "purpose": purpose,
            "difficulty_level": difficulty_level,
            "target_weeks": target_weeks,
            "weekly_available_hours": weekly_available_hours,
            "preferred_learning_style": preferred_learning_style,
        }

    def _normalized_success_result(self):
        """View 테스트에서 저장 service mock에 전달할 정규화 성공 응답을 만든다."""
        return {
            "status": "success",
            "title": "Python roadmap",
            "recommendation_reason": "학습 목표에 맞춘 추천입니다.",
            "user_profile": {
                "goal": "Python 배우기",
                "target_weeks": 8,
                "weekly_hours": 10,
                "difficulty_level": "beginner",
                "preferred_learning_style": "project",
            },
            "steps": [],
        }


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
        self.assertEqual(response.data["status"], "NOT_STARTED")
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
