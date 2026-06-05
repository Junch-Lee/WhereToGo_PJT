from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.accounts.models import Topic, UserInterestTopic, UserProfile
from apps.curriculum.models import (
    Category,
    Curriculum,
    CurriculumCourse,
    CurriculumStepCourse,
    CurriculumStepResource,
    LearningResource,
)
from apps.curriculum.services.curriculum_create_service import create_curriculum_for_user


SEED_PASSWORD = "testpass123"


class Command(BaseCommand):
    help = "개발 검증용 사용자와 커리큘럼 테스트 데이터를 생성합니다."

    seed_users = [
        {
            "email": "user_backend@example.com",
            "nickname": "백엔드 학습자",
            "available_weekly_hours": 10,
            "preferred_learning_style": "project",
            "topic_slugs": ["django", "rest-api"],
            "goals": [
                {
                    "goal": "Django REST API 백엔드 포트폴리오를 만들고 싶어",
                    "target_weeks": 8,
                    "weekly_available_hours": 10,
                    "preferred_learning_style": "project",
                },
                {
                    "goal": "인증과 배포까지 포함한 백엔드 프로젝트를 완성하고 싶어",
                    "target_weeks": 6,
                    "preferred_learning_style": "practice",
                },
            ],
        },
        {
            "email": "user_data@example.com",
            "nickname": "데이터 학습자",
            "available_weekly_hours": 6,
            "preferred_learning_style": "practice",
            "topic_slugs": ["sql", "python-data"],
            "goals": [
                {
                    "goal": "SQL과 Python으로 데이터 분석 기초를 배우고 싶어",
                    "target_weeks": 6,
                    "preferred_learning_style": "practice",
                },
                {
                    "goal": "데이터 시각화와 리포트 작성까지 연습하고 싶어",
                    "target_weeks": 4,
                },
            ],
        },
        {
            "email": "user_ai@example.com",
            "nickname": "AI 학습자",
            "available_weekly_hours": 12,
            "preferred_learning_style": "theory",
            "topic_slugs": ["machine-learning", "deep-learning"],
            "goals": [
                {
                    "goal": "머신러닝 입문 이론과 실습 커리큘럼을 만들고 싶어",
                    "target_weeks": 10,
                },
                {
                    "goal": "딥러닝 모델 학습 흐름을 프로젝트로 익히고 싶어",
                    "target_weeks": 8,
                    "preferred_learning_style": "project",
                },
            ],
        },
    ]

    def handle(self, *args, **options):
        """
        개발자가 프론트 화면과 DB 저장 흐름을 빠르게 확인할 수 있도록 시드 데이터를 만든다.

        이 명령은 실제 운영 데이터 생성을 위한 도구가 아니다. 로컬 개발 DB에서 로그인 가능한
        테스트 사용자 3명을 만들고, 각 사용자별 관심 분야와 선호 학습 방식이 다른 커리큘럼을
        생성해 사이드바/마이페이지/API 응답을 직접 확인하는 목적이다.

        재실행 정책:
            같은 이메일의 시드 사용자가 이미 있으면 비밀번호와 프로필을 다시 맞춘다.
            해당 시드 사용자들이 가진 기존 커리큘럼은 삭제한 뒤 새로 생성한다. 이렇게 해야
            여러 번 실행해도 커리큘럼 수가 계속 늘어나지 않고, 화면 검증 결과를 예측할 수 있다.
        """
        self.create_education_seed_data()

        for user_data in self.seed_users:
            user = self.create_or_update_user(user_data)
            self.reset_user_curriculums(user)
            self.update_user_profile(user, user_data)
            self.update_user_interest_topics(user, user_data["topic_slugs"])

            created_curriculums = [
                create_curriculum_for_user(user, goal_payload)
                for goal_payload in user_data["goals"]
            ]
            self.print_user_summary(user, created_curriculums)

        self.print_login_summary()

    def create_or_update_user(self, user_data):
        """
        로그인 가능한 시드 사용자를 생성하거나 기존 사용자의 기본 정보를 갱신한다.

        모든 시드 사용자는 같은 비밀번호를 사용한다. 프론트 로그인 화면에서 여러 계정으로
        빠르게 전환해 사용자별 커리큘럼 격리가 잘 되는지 확인하기 위한 선택이다.
        """
        User = get_user_model()
        user, _ = User.objects.get_or_create(
            email=user_data["email"],
            defaults={
                "nickname": user_data["nickname"],
                "agree_terms": True,
            },
        )
        user.nickname = user_data["nickname"]
        user.agree_terms = True
        user.set_password(SEED_PASSWORD)
        user.save(update_fields=["nickname", "agree_terms", "password"])
        return user

    def reset_user_curriculums(self, user):
        """
        시드 사용자의 기존 커리큘럼을 삭제한다.

        삭제 대상은 현재 명령이 관리하는 3명의 테스트 사용자 데이터로 제한한다. 다른 실제
        개발 계정의 커리큘럼은 건드리지 않기 위해 전체 테이블 초기화는 사용하지 않는다.
        """
        Curriculum.objects.filter(user=user).delete()

    def update_user_profile(self, user, user_data):
        """
        사용자 프로필 fallback 검증에 필요한 주간 학습 가능 시간과 선호 학습 방식을 저장한다.
        """
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "available_weekly_hours": user_data["available_weekly_hours"],
                "preferred_learning_style": user_data["preferred_learning_style"],
            },
        )

    def update_user_interest_topics(self, user, topic_slugs):
        """
        마이페이지 프로필에서 관심 학습 분야를 확인할 수 있도록 사용자별 관심 주제를 연결한다.
        """
        UserInterestTopic.objects.filter(user=user).delete()
        topics = Topic.objects.filter(slug__in=topic_slugs)

        for topic in topics:
            UserInterestTopic.objects.get_or_create(user=user, topic=topic)

    def create_education_seed_data(self):
        """
        커리큘럼 생성 service가 관련 교육 데이터를 찾을 수 있도록 최소 기준 데이터를 만든다.

        생성 대상:
            - Category: 백엔드, 데이터, AI
            - Topic: Django, REST API, SQL, Python 데이터 분석, 머신러닝, 딥러닝
            - LearningResource: 목표별 추천 자료
            - CurriculumCourse: 목표별 추천 강의

        관련 데이터가 있으면 저장 service가 curriculum_categories, curriculum_step_resources,
        curriculum_step_courses 연결 row까지 생성하는지 함께 확인할 수 있다.
        """
        categories = [
            ("backend", "백엔드", "Django와 REST API 백엔드 학습"),
            ("data", "데이터", "SQL과 Python 데이터 분석 학습"),
            ("ai", "AI", "머신러닝과 딥러닝 입문 학습"),
        ]
        for slug, name, description in categories:
            Category.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "description": description},
            )

        topics = [
            ("Django", "django", "Django 백엔드 프레임워크"),
            ("REST API", "rest-api", "REST API 설계와 구현"),
            ("SQL", "sql", "데이터 조회와 집계"),
            ("Python 데이터 분석", "python-data", "Python 기반 데이터 분석"),
            ("머신러닝", "machine-learning", "머신러닝 입문"),
            ("딥러닝", "deep-learning", "딥러닝 모델 학습"),
        ]
        for name, slug, description in topics:
            Topic.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "topic_type": Topic.TopicType.SKILL,
                    "description": description,
                    "is_active": True,
                },
            )

        resources = [
            (
                "Django REST API 프로젝트 가이드",
                "Django REST API 백엔드 포트폴리오 실습 자료",
                "project",
            ),
            (
                "SQL Python 데이터 분석 실습 노트",
                "SQL과 Python으로 데이터 분석을 연습하는 자료",
                "practice",
            ),
            (
                "머신러닝 입문 이론 정리",
                "머신러닝 핵심 개념과 학습 흐름을 정리한 자료",
                "text",
            ),
            (
                "딥러닝 프로젝트 체크리스트",
                "딥러닝 모델 학습 프로젝트를 진행할 때 확인할 항목",
                "project",
            ),
        ]
        for title, description, resource_type in resources:
            LearningResource.objects.update_or_create(
                title=title,
                defaults={
                    "description": description,
                    "provider": "WhereToGo Seed",
                    "resource_type": resource_type,
                },
            )

        courses = [
            (
                "Django REST API 백엔드 강의",
                "Django로 인증, CRUD, 배포가 포함된 백엔드 포트폴리오를 만든다.",
            ),
            (
                "SQL Python 데이터 분석 강의",
                "SQL과 Python으로 데이터를 조회, 분석, 시각화한다.",
            ),
            (
                "머신러닝 입문 강의",
                "머신러닝 핵심 알고리즘과 모델 학습 흐름을 이해한다.",
            ),
            (
                "딥러닝 프로젝트 강의",
                "딥러닝 모델을 학습하고 결과를 해석하는 프로젝트를 수행한다.",
            ),
        ]
        for course_name, learning_objective in courses:
            CurriculumCourse.objects.update_or_create(
                course_name=course_name,
                defaults={
                    "learning_objective": learning_objective,
                    "description": learning_objective,
                },
            )

    def print_user_summary(self, user, curriculums):
        """
        생성 결과를 사용자별로 출력한다.

        출력값은 API 검증용 요약이다. 각 Curriculum의 step 수와 선택 연결 테이블 row 수를 함께
        보여줘서 DB 저장 범위를 빠르게 확인할 수 있다.
        """
        curriculum_ids = [curriculum.id for curriculum in curriculums]
        step_ids = [
            step_id
            for curriculum in curriculums
            for step_id in curriculum.steps.values_list("id", flat=True)
        ]

        self.stdout.write(f"[User] {user.email}")
        self.stdout.write(f"- Curriculum: {len(curriculum_ids)}개 생성")
        self.stdout.write(f"- Steps: {len(step_ids)}개 생성")
        self.stdout.write(
            f"- StepResources: "
            f"{CurriculumStepResource.objects.filter(curriculum_step_id__in=step_ids).count()}개 생성"
        )
        self.stdout.write(
            f"- StepCourses: "
            f"{CurriculumStepCourse.objects.filter(curriculum_step_id__in=step_ids).count()}개 생성"
        )
        self.stdout.write(
            f"- Total user curriculums: {Curriculum.objects.filter(user=user).count()}개"
        )

    def print_login_summary(self):
        """
        프론트 로그인 검증에 바로 사용할 수 있도록 계정 정보를 마지막에 모아서 출력한다.
        """
        self.stdout.write("")
        self.stdout.write("[로그인 정보]")
        for user_data in self.seed_users:
            self.stdout.write(f"- {user_data['email']} / {SEED_PASSWORD}")
