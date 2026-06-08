"""
커리큘럼 생성에 필요한 입력 context를 구성하는 service.

요청 body, 사용자 프로필 fallback, 목표 키워드, 관련 교육 데이터 후보를 한 곳에서 모은다.
생성기와 저장 service는 이 context를 읽기만 하므로, fallback 우선순위나 검색 방식이 바뀌어도
변경 범위를 이 파일로 제한할 수 있다.
"""

import re

from django.db.models import Q

from apps.accounts.models import Topic, UserProfile
from apps.curriculum.models import Category, CurriculumCourse, LearningResource


def resolve_target_weeks(request_value):
    """
    커리큘럼 목표 기간을 결정한다.

    입력값:
        request_value: POST 요청 body의 target_weeks 값. 없을 수 있다.

    반환값:
        커리큘럼 생성과 저장에 사용할 주 단위 기간.

    현재 구현:
        요청 값이 있으면 그대로 사용하고, 없으면 서비스 기본값 8주를 사용한다.

    향후 확장 지점:
        진단 결과나 AI/Agent 계획 결과로 기간을 보정해야 한다면, 우선순위를
        흩뜨리지 않고 이 함수 안에서만 조정한다.
    """
    return request_value or 8


def resolve_weekly_available_hours(request_value, user_profile):
    """
    주간 학습 가능 시간을 우선순위에 따라 결정한다.

    우선순위:
        1. POST 요청 body의 weekly_available_hours
        2. user_profile.available_weekly_hours
        3. 서비스 기본값 7

    입력값:
        request_value: 요청 body에서 받은 선택 값.
        user_profile: 현재 사용자 프로필. 없을 수 있다.

    반환값:
        생성기와 Curriculum 저장에 사용할 정수 시간 값.
    """
    if request_value:
        return request_value

    if user_profile and user_profile.available_weekly_hours:
        return user_profile.available_weekly_hours

    return 7


def resolve_preferred_learning_style(request_value, user_profile):
    """
    선호 학습 방식을 우선순위에 따라 결정한다.

    우선순위:
        1. POST 요청 body의 preferred_learning_style
        2. user_profile.preferred_learning_style
        3. 서비스 기본값 "balanced"

    현재 구현:
        선호 학습 방식은 API 입력값이면서 동시에 생성 context의 일부다. 따라서
        view나 serializer가 아니라 service 계층에서 fallback을 확정한다.

    향후 확장 지점:
        AI/RAG/Agent 생성기는 이 함수가 확정한 값을 context에서 읽어 사용하면
        된다. 우선순위가 바뀌더라도 생성기나 view를 수정하지 않도록 한다.
    """
    if request_value:
        return request_value

    if user_profile and user_profile.preferred_learning_style:
        return user_profile.preferred_learning_style

    return "balanced"


def extract_goal_keywords(goal):
    """
    사용자의 학습 목표에서 간단한 검색 키워드를 추출한다.

    입력값:
        goal: 사용자가 입력한 필수 학습 목표 문자열.

    반환값:
        DB 검색에 사용할 최대 8개의 키워드 목록.

    현재 구현:
        외부 AI, 벡터 DB, RAG 검색을 사용하지 않기 위해 정규식 기반의 단순
        토큰 추출만 수행한다.

    향후 확장 지점:
        이 함수는 임베딩 검색, BM25, Agent 기반 query rewriting으로 교체하기
        쉬운 경계다. 반환값 형태를 유지하면 아래 ORM 검색 흐름을 점진적으로
        바꿀 수 있다.
    """
    words = re.findall(r"[A-Za-z0-9가-힣+#.]+", goal.lower())
    return [word for word in words if len(word) >= 2][:8]


def build_search_query(fields, keywords):
    """
    여러 필드에 대해 키워드 OR 검색 조건을 만든다.

    입력값:
        fields: icontains 검색을 적용할 모델 필드명 목록.
        keywords: goal에서 추출한 키워드 목록.

    반환값:
        Django ORM filter에 넘길 Q 객체.

    주의:
        키워드가 없을 때는 호출자가 빈 queryset을 사용한다. 의도치 않게 전체
        교육 데이터 테이블을 훑지 않기 위해서다.
    """
    query = Q()

    for keyword in keywords:
        field_query = Q()
        for field in fields:
            field_query |= Q(**{f"{field}__icontains": keyword})
        query |= field_query

    return query


def build_curriculum_context(user, validated_data):
    """
    커리큘럼 생성을 위해 필요한 context를 만든다.

    입력값:
        user: 인증된 요청 사용자.
        validated_data: CurriculumCreateSerializer를 통과한 요청 데이터.

    반환값:
        정규화된 사용자 입력, 프로필 fallback 값, goal 키워드, 관련 교육 데이터
        후보를 담은 dict.

    현재 구현:
        user_profile을 조회해 fallback 값을 확정하고, goal 키워드로 Course,
        Resource, Topic, Category를 단순 ORM 검색한다. 관련 교육 데이터가 없어도
        커리큘럼 생성은 계속 진행된다.

    향후 확장 지점:
        courses/resources/topics/categories를 채우는 검색 부분이 RAG 또는 Agent
        검색으로 교체될 위치다. 반환 key를 유지하면 생성기와 저장 service는
        그대로 둘 수 있다.
    """
    user_profile = UserProfile.objects.filter(user=user).first()
    goal = validated_data["goal"].strip()
    target_weeks = resolve_target_weeks(validated_data.get("target_weeks"))
    weekly_available_hours = resolve_weekly_available_hours(
        validated_data.get("weekly_available_hours"),
        user_profile,
    )
    preferred_learning_style = resolve_preferred_learning_style(
        validated_data.get("preferred_learning_style"),
        user_profile,
    )
    keywords = extract_goal_keywords(goal)

    courses = CurriculumCourse.objects.none()
    resources = LearningResource.objects.none()
    topics = Topic.objects.none()
    categories = Category.objects.none()

    if keywords:
        courses = CurriculumCourse.objects.filter(
            build_search_query(
                ("course_name", "learning_objective", "description"),
                keywords,
            )
        ).order_by("id")[:12]
        resources = LearningResource.objects.filter(
            build_search_query(("title", "description"), keywords)
        ).order_by("id")[:12]
        topics = Topic.objects.filter(
            build_search_query(("name", "description"), keywords),
            is_active=True,
        ).order_by("id")[:12]
        categories = Category.objects.filter(
            build_search_query(("name", "description"), keywords)
        ).order_by("id")[:4]

    return {
        "user_profile": user_profile,
        "goal": goal,
        "target_weeks": target_weeks,
        "weekly_available_hours": weekly_available_hours,
        "preferred_learning_style": preferred_learning_style,
        "keywords": keywords,
        "courses": list(courses),
        "resources": list(resources),
        "topics": list(topics),
        "categories": list(categories),
    }
