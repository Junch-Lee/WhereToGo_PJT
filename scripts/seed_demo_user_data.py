from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.accounts.models import Topic, TopicAlias, UserInterestTopic, UserProfile
from apps.curriculum.models import (
    Category,
    CourseTopic,
    Curriculum,
    CurriculumCategory,
    CurriculumCourse,
    CurriculumStep,
    CurriculumStepCourse,
    CurriculumStepProgress,
    CurriculumStepResource,
    LearningProgress,
    LearningResource,
    LearningSchedule,
    ResourceTopic,
)


EMAIL = "demo.learner@wheretogo.test"
PASSWORD = "DemoPass123!"


def main() -> None:
    user = create_user()
    reset_user_data(user)
    data = create_reference_data()
    create_curricula(user, data)
    print_summary(user)


def create_user():
    User = get_user_model()
    user, _ = User.objects.get_or_create(
        email=EMAIL,
        defaults={"nickname": "발표용 학습자", "agree_terms": True},
    )
    user.nickname = "발표용 학습자"
    user.agree_terms = True
    user.is_active = True
    user.set_password(PASSWORD)
    user.save()

    UserProfile.objects.update_or_create(
        user=user,
        defaults={
            "available_weekly_hours": 10,
            "preferred_learning_style": "project",
        },
    )
    return user


def reset_user_data(user) -> None:
    Curriculum.objects.filter(user=user).delete()
    UserInterestTopic.objects.filter(user=user).delete()


def create_reference_data() -> dict:
    topics = {
        "python": upsert_topic("Python", "python", "프로그래밍과 데이터 처리를 위한 Python 기초"),
        "data": upsert_topic("데이터 분석", "data-analysis", "데이터 수집, 전처리, 분석, 시각화"),
        "ml": upsert_topic("머신러닝", "machine-learning", "지도학습, 비지도학습, 모델 평가"),
        "django": upsert_topic("Django", "django", "Django 기반 웹 백엔드 개발"),
        "rest": upsert_topic("REST API", "rest-api", "RESTful API 설계와 구현"),
        "algorithm": upsert_topic("알고리즘", "algorithm", "문제 해결과 자료구조/알고리즘"),
        "sql": upsert_topic("SQL", "sql", "관계형 데이터베이스 조회와 모델링"),
        "portfolio": upsert_topic("포트폴리오", "portfolio-project", "취업/발표용 프로젝트 정리"),
    }

    for topic, alias in [
        (topics["ml"], "ML"),
        (topics["ml"], "기계학습"),
        (topics["data"], "데이터 시각화"),
        (topics["rest"], "API"),
        (topics["django"], "장고"),
        (topics["algorithm"], "코딩테스트"),
    ]:
        TopicAlias.objects.get_or_create(
            topic=topic,
            alias_name=alias,
            match_policy="contains",
            defaults={"source": "demo", "language": "ko"},
        )

    categories = {}
    for slug, name, description in [
        ("data-ai", "데이터/AI", "Python, 데이터 분석, 머신러닝 학습 영역"),
        ("backend", "백엔드", "Django와 REST API 기반 웹 백엔드 학습 영역"),
        ("algorithm", "알고리즘", "코딩테스트와 문제 해결 학습 영역"),
        ("career", "커리어/포트폴리오", "프로젝트 정리와 취업 준비 학습 영역"),
    ]:
        categories[slug], _ = Category.objects.update_or_create(
            slug=slug,
            defaults={"name": name, "description": description},
        )

    resources = create_resources()
    courses = create_courses()
    link_resource_topics(resources, topics)
    link_course_topics(courses, topics)
    return {"topics": topics, "categories": categories, "resources": resources, "courses": courses}


def upsert_topic(name: str, slug: str, description: str):
    topic, _ = Topic.objects.update_or_create(
        slug=slug,
        defaults={
            "name": name,
            "depth": 2,
            "topic_type": Topic.TopicType.SKILL,
            "is_learning_unit": True,
            "is_assessable": True,
            "description": description,
            "is_active": True,
        },
    )
    return topic


def create_resources() -> dict:
    resources = {}
    rows = [
        ("python-basic-lab", "Python 기초 실습 노트", "변수, 조건문, 반복문, 함수까지 빠르게 복습하는 실습 자료", "K-MOOC", "practice", "beginner", "https://example.com/python-basic"),
        ("pandas-eda-guide", "Pandas EDA 체크리스트", "데이터 로딩, 결측치, 그룹화, 시각화 흐름을 정리한 자료", "KOCW", "text", "intermediate", "https://example.com/pandas-eda"),
        ("ml-basic-course", "머신러닝 입문 강의", "회귀, 분류, 모델 평가 지표를 다루는 입문 강의", "K-MOOC", "video", "intermediate", "https://example.com/ml-basic"),
        ("django-crud-lab", "Django CRUD 프로젝트 실습", "모델, 뷰, 라우팅, 인증을 연결하는 미니 프로젝트", "WhereToGo", "project", "intermediate", "https://example.com/django-crud"),
        ("drf-api-design", "DRF API 설계 가이드", "Serializer, View, 권한, pagination을 실습하는 자료", "WhereToGo", "text", "intermediate", "https://example.com/drf-api"),
        ("algorithm-daily", "알고리즘 데일리 문제집", "정렬, 탐색, 그래프 기본 문제를 매일 풀 수 있는 문제집", "Baekjoon", "practice", "beginner", "https://example.com/algorithm-daily"),
        ("sql-reporting", "SQL 리포팅 실습", "JOIN, GROUP BY, window function을 리포트 예제로 연습", "KOCW", "practice", "intermediate", "https://example.com/sql-reporting"),
        ("portfolio-readme", "개발자 포트폴리오 README 템플릿", "프로젝트 문제 정의, 아키텍처, 트러블슈팅을 정리하는 템플릿", "WhereToGo", "text", "beginner", "https://example.com/portfolio-readme"),
    ]
    for lookup_key, title, description, provider, resource_type, difficulty, url in rows:
        resources[lookup_key], _ = LearningResource.objects.update_or_create(
            lookup_key=lookup_key,
            defaults={
                "title": title,
                "description": description,
                "provider": provider,
                "provider_name": provider,
                "resource_type": resource_type,
                "difficulty_level": difficulty,
                "url": url,
            },
        )
    return resources


def create_courses() -> dict:
    courses = {}
    rows = [
        (91001, "Python 프로그래밍과 데이터 처리", "한국공개SW대학", "컴퓨터공학과", "Python 문법과 파일/데이터 처리 기초를 학습한다."),
        (91002, "데이터 분석 실무", "한국데이터대학", "데이터사이언스학과", "Pandas 기반 탐색적 분석과 시각화 리포트를 작성한다."),
        (91003, "머신러닝 개론", "AI융합대학교", "인공지능학과", "회귀/분류 모델을 학습하고 성능을 평가한다."),
        (91004, "Django 웹 백엔드 개발", "웹서비스대학교", "소프트웨어학과", "Django와 DRF로 인증 포함 REST API를 구현한다."),
        (91005, "알고리즘 문제 해결", "알고리즘대학교", "컴퓨터공학과", "자료구조와 기본 알고리즘을 문제 풀이로 학습한다."),
        (91006, "SQL과 데이터베이스 활용", "데이터베이스대학교", "정보시스템학과", "관계형 데이터 모델과 SQL 리포팅을 실습한다."),
        (91007, "개발 포트폴리오 설계", "커리어대학교", "소프트웨어융합학과", "프로젝트 경험을 포트폴리오와 발표 자료로 구조화한다."),
    ]
    for source_row_number, course_name, university, department, objective in rows:
        courses[source_row_number], _ = CurriculumCourse.objects.update_or_create(
            source_row_number=source_row_number,
            defaults={
                "course_name": course_name,
                "university_name": university,
                "department_name": department,
                "grade": 3,
                "semester": "1학기",
                "learning_objective": objective,
                "description": objective,
            },
        )
    return courses


def link_resource_topics(resources: dict, topics: dict) -> None:
    links = {
        "python-basic-lab": ["python"],
        "pandas-eda-guide": ["python", "data"],
        "ml-basic-course": ["ml", "data"],
        "django-crud-lab": ["django"],
        "drf-api-design": ["django", "rest"],
        "algorithm-daily": ["algorithm"],
        "sql-reporting": ["sql", "data"],
        "portfolio-readme": ["portfolio"],
    }
    for resource_key, topic_keys in links.items():
        for index, topic_key in enumerate(topic_keys):
            ResourceTopic.objects.update_or_create(
                learning_resource=resources[resource_key],
                topic=topics[topic_key],
                defaults={
                    "relevance_score": "0.90",
                    "extraction_method": "demo",
                    "is_primary": index == 0,
                    "link_type": "seed",
                },
            )


def link_course_topics(courses: dict, topics: dict) -> None:
    links = {
        91001: ["python"],
        91002: ["data", "python"],
        91003: ["ml"],
        91004: ["django", "rest"],
        91005: ["algorithm"],
        91006: ["sql", "data"],
        91007: ["portfolio"],
    }
    for source_row_number, topic_keys in links.items():
        for index, topic_key in enumerate(topic_keys):
            CourseTopic.objects.update_or_create(
                curriculum_course=courses[source_row_number],
                topic=topics[topic_key],
                defaults={
                    "relevance_score": "0.90",
                    "extraction_method": "demo",
                    "is_primary": index == 0,
                    "link_type": "seed",
                },
            )


def create_curricula(user, data: dict) -> None:
    topics = data["topics"]
    categories = data["categories"]
    resources = data["resources"]
    courses = data["courses"]

    for key in ["python", "data", "ml", "django", "rest", "algorithm", "sql", "portfolio"]:
        UserInterestTopic.objects.get_or_create(user=user, topic=topics[key])

    now = timezone.now()
    today = timezone.localdate()

    def curriculum(title, goal, status, weeks, hours, difficulty, style, category_key, reason):
        obj = Curriculum.objects.create(
            user=user,
            title=title,
            goal=goal,
            status=status,
            target_weeks=weeks,
            weekly_available_hours=hours,
            difficulty_level=difficulty,
            preferred_learning_style=style,
            recommendation_reason=reason,
        )
        CurriculumCategory.objects.create(curriculum=obj, category=categories[category_key], is_primary=True)
        return obj

    def step(curriculum_obj, order, title, description, topic_key, difficulty, hours, resource_keys, course_keys, prereq=""):
        obj = CurriculumStep.objects.create(
            curriculum=curriculum_obj,
            step_order=order,
            title=title,
            description=description,
            target_topic=topics[topic_key],
            difficulty_level=difficulty,
            estimated_hours=hours,
            prerequisite_note=prereq,
        )
        for index, resource_key in enumerate(resource_keys, 1):
            CurriculumStepResource.objects.create(
                curriculum_step=obj,
                learning_resource=resources[resource_key],
                reason=f"{title} 단계에서 바로 참고하기 좋은 자료입니다.",
                sort_order=index,
            )
        for index, source_row_number in enumerate(course_keys, 1):
            CurriculumStepCourse.objects.create(
                curriculum_step=obj,
                curriculum_course=courses[source_row_number],
                reason=f"{title} 학습 목표와 연결되는 강의입니다.",
                sort_order=index,
            )
        return obj

    def progress(curriculum_obj, step_obj, status, rate, minutes, studied_days_ago=None, completed_days_ago=None, schedule_offset=0, schedule_status=LearningSchedule.Status.DONE, memo=""):
        studied_at = today - timedelta(days=studied_days_ago) if studied_days_ago is not None else None
        completed_at = now - timedelta(days=completed_days_ago) if completed_days_ago is not None else None
        started_at = now - timedelta(days=(studied_days_ago or completed_days_ago or 0) + 2)
        last_studied_at = (
            timezone.make_aware(datetime.combine(studied_at, datetime.min.time()))
            if studied_at
            else completed_at
        )
        progress_obj = CurriculumStepProgress.objects.create(
            curriculum=curriculum_obj,
            curriculum_step=step_obj,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            progress_rate=rate,
            actual_minutes=minutes,
            last_studied_at=last_studied_at,
        )
        schedule_obj = LearningSchedule.objects.create(
            curriculum_step=step_obj,
            step_progress=progress_obj,
            week_no=max(1, step_obj.step_order),
            sequence_no=step_obj.step_order,
            scheduled_date=today + timedelta(days=schedule_offset),
            planned_hours=max(1, round(step_obj.estimated_hours / 2)),
            status=schedule_status,
        )
        if studied_at:
            LearningProgress.objects.create(
                learning_schedule=schedule_obj,
                curriculum_step=step_obj,
                step_progress=progress_obj,
                status=LearningProgress.Status.COMPLETED
                if status == CurriculumStepProgress.Status.COMPLETED
                else LearningProgress.Status.PARTIAL,
                actual_minutes=minutes,
                progress_rate=rate,
                studied_at=studied_at,
                started_at=started_at,
                completed_at=completed_at or now - timedelta(days=studied_days_ago),
                memo=memo,
            )
        return progress_obj

    data_curriculum = curriculum(
        "Python과 데이터 분석 실무 커리큘럼",
        "3개월 안에 Python, Pandas, 머신러닝 기초를 익혀 데이터 분석 포트폴리오를 만들고 싶다.",
        Curriculum.Status.ACTIVE,
        12,
        10,
        "intermediate",
        "project",
        "data-ai",
        "Python 기초부터 EDA와 머신러닝까지 이어지는 실습 중심 경로입니다.",
    )
    s11 = step(data_curriculum, 1, "Python 핵심 문법 복습", "데이터 분석에 필요한 Python 문법을 빠르게 정리합니다.", "python", "beginner", 5, ["python-basic-lab"], [91001])
    s12 = step(data_curriculum, 2, "Pandas로 탐색적 데이터 분석하기", "CSV 데이터를 불러와 결측치, 그룹화, 시각화를 연습합니다.", "data", "intermediate", 8, ["pandas-eda-guide", "sql-reporting"], [91002, 91006])
    s13 = step(data_curriculum, 3, "머신러닝 모델 첫 실험", "회귀/분류 모델을 학습하고 평가 지표를 해석합니다.", "ml", "intermediate", 10, ["ml-basic-course"], [91003], "Python과 Pandas 기본 조작을 먼저 익히면 좋습니다.")
    step(data_curriculum, 4, "분석 결과 포트폴리오 정리", "분석 과정과 결과를 README와 발표 자료로 정리합니다.", "portfolio", "intermediate", 6, ["portfolio-readme"], [91007])
    progress(data_curriculum, s11, CurriculumStepProgress.Status.COMPLETED, 100, 330, 8, 8, -8, memo="Python 문법과 함수 파트를 복습 완료")
    progress(data_curriculum, s12, CurriculumStepProgress.Status.COMPLETED, 100, 520, 3, 3, -3, memo="결측치 처리와 groupby 실습 완료")
    p13 = progress(data_curriculum, s13, CurriculumStepProgress.Status.IN_PROGRESS, 45, 210, 1, None, 0, LearningSchedule.Status.PLANNED, "로지스틱 회귀 예제까지 진행")
    LearningSchedule.objects.create(curriculum_step=s13, step_progress=p13, week_no=3, sequence_no=2, scheduled_date=today + timedelta(days=2), planned_hours=2, status=LearningSchedule.Status.PLANNED)
    data_curriculum.current_step = s13
    data_curriculum.started_at = now - timedelta(days=15)
    data_curriculum.save()

    backend_curriculum = curriculum(
        "Django REST API 백엔드 포트폴리오",
        "Django와 DRF로 인증, CRUD, 배포 준비가 포함된 백엔드 포트폴리오를 완성한다.",
        Curriculum.Status.COMPLETED,
        8,
        9,
        "intermediate",
        "project",
        "backend",
        "백엔드 프로젝트 완성에 필요한 Django, DRF, API 설계를 순서대로 학습했습니다.",
    )
    s21 = step(backend_curriculum, 1, "Django 프로젝트 구조 잡기", "앱 분리, 모델 설계, URL 구조를 정리합니다.", "django", "beginner", 5, ["django-crud-lab"], [91004])
    s22 = step(backend_curriculum, 2, "DRF Serializer와 View 구현", "Serializer, View, 권한 처리를 연결해 API를 만듭니다.", "rest", "intermediate", 8, ["drf-api-design"], [91004])
    s23 = step(backend_curriculum, 3, "인증과 API 문서 정리", "JWT 인증과 Swagger 문서를 연결합니다.", "rest", "intermediate", 6, ["drf-api-design", "portfolio-readme"], [91004, 91007])
    progress(backend_curriculum, s21, CurriculumStepProgress.Status.COMPLETED, 100, 300, 25, 25, -25, memo="Django 모델과 URL 구조 정리")
    progress(backend_curriculum, s22, CurriculumStepProgress.Status.COMPLETED, 100, 460, 18, 18, -18, memo="Serializer와 권한 처리 구현 완료")
    progress(backend_curriculum, s23, CurriculumStepProgress.Status.COMPLETED, 100, 390, 12, 12, -12, memo="JWT와 API 문서 연결 완료")
    backend_curriculum.current_step = s23
    backend_curriculum.started_at = now - timedelta(days=30)
    backend_curriculum.completed_at = now - timedelta(days=12)
    backend_curriculum.save()

    algorithm_curriculum = curriculum(
        "코딩테스트 알고리즘 루틴",
        "매일 1문제씩 풀면서 정렬, 탐색, 그래프 기본기를 회복한다.",
        Curriculum.Status.PAUSED,
        6,
        5,
        "beginner",
        "practice",
        "algorithm",
        "짧은 시간 안에 문제 풀이 감각을 회복하기 위한 루틴형 커리큘럼입니다.",
    )
    s31 = step(algorithm_curriculum, 1, "정렬과 완전탐색 복습", "정렬 기준과 완전탐색 문제 패턴을 정리합니다.", "algorithm", "beginner", 5, ["algorithm-daily"], [91005])
    s32 = step(algorithm_curriculum, 2, "BFS/DFS 기본 문제 풀기", "그래프 탐색 문제를 유형별로 연습합니다.", "algorithm", "intermediate", 7, ["algorithm-daily"], [91005])
    step(algorithm_curriculum, 3, "실전 모의고사 풀이", "제한 시간 안에 여러 유형을 섞어 풉니다.", "algorithm", "intermediate", 6, ["algorithm-daily"], [91005])
    progress(algorithm_curriculum, s31, CurriculumStepProgress.Status.COMPLETED, 100, 260, 20, 20, -20, memo="정렬과 완전탐색 12문제 풀이")
    progress(algorithm_curriculum, s32, CurriculumStepProgress.Status.PAUSED, 35, 130, 10, None, -10, LearningSchedule.Status.MISSED, "DFS 재귀 구현에서 잠시 중단")
    algorithm_curriculum.current_step = s32
    algorithm_curriculum.started_at = now - timedelta(days=22)
    algorithm_curriculum.paused_at = now - timedelta(days=9)
    algorithm_curriculum.save()

    sql_curriculum = curriculum(
        "SQL 리포팅 역량 강화",
        "서비스 데이터를 SQL로 조회하고 지표 리포트를 만들 수 있게 된다.",
        Curriculum.Status.DRAFT,
        4,
        6,
        "beginner",
        "practice",
        "data-ai",
        "SQL 집계와 리포팅 역량을 짧게 강화하는 계획입니다.",
    )
    step(sql_curriculum, 1, "SELECT/JOIN 복습", "기본 조회와 JOIN을 복습합니다.", "sql", "beginner", 4, ["sql-reporting"], [91006])
    step(sql_curriculum, 2, "집계와 리포트 쿼리", "GROUP BY와 window function으로 지표를 만듭니다.", "sql", "intermediate", 6, ["sql-reporting"], [91006])

    career_curriculum = curriculum(
        "개발자 포트폴리오 발표 준비",
        "프로젝트 README와 발표 흐름을 정리해 최종 시연을 안정적으로 준비한다.",
        Curriculum.Status.ACTIVE,
        3,
        7,
        "intermediate",
        "balanced",
        "career",
        "완성한 기능을 심사자가 이해하기 쉬운 이야기와 자료로 정리하는 경로입니다.",
    )
    s51 = step(career_curriculum, 1, "프로젝트 문제 정의 정리", "서비스가 해결하려는 문제와 사용자 페르소나를 정리합니다.", "portfolio", "beginner", 3, ["portfolio-readme"], [91007])
    s52 = step(career_curriculum, 2, "기술 의사결정 정리", "RAG, Agent, ERD 의사결정을 발표 흐름에 맞게 정리합니다.", "portfolio", "intermediate", 4, ["portfolio-readme", "drf-api-design"], [91007])
    step(career_curriculum, 3, "시연 스크립트 리허설", "커리큘럼 생성부터 학습 대시보드까지 시연 순서를 연습합니다.", "portfolio", "intermediate", 4, ["portfolio-readme"], [91007])
    progress(career_curriculum, s51, CurriculumStepProgress.Status.COMPLETED, 100, 160, 2, 2, -2, memo="README의 서비스 목표와 핵심 기능 정리")
    progress(career_curriculum, s52, CurriculumStepProgress.Status.IN_PROGRESS, 60, 150, 0, None, 1, LearningSchedule.Status.PLANNED, "RAG와 Agent 의사결정 정리 중")
    career_curriculum.current_step = s52
    career_curriculum.started_at = now - timedelta(days=4)
    career_curriculum.save()


def print_summary(user) -> None:
    print("DEMO_USER_CREATED")
    print(f"email={EMAIL}")
    print(f"password={PASSWORD}")
    print(f"curricula={Curriculum.objects.filter(user=user).count()}")
    print(f"steps={CurriculumStep.objects.filter(curriculum__user=user).count()}")
    print(f"progresses={CurriculumStepProgress.objects.filter(curriculum__user=user).count()}")
    print(f"schedules={LearningSchedule.objects.filter(curriculum_step__curriculum__user=user).count()}")
    print(f"learning_progresses={LearningProgress.objects.filter(curriculum_step__curriculum__user=user).count()}")


if __name__ == "__main__":
    main()
