def build_step_titles(goal, target_weeks):
    """
    현재 임시 생성기에서 사용할 주차별 step 제목을 만든다.

    입력값:
        goal: 사용자가 입력한 학습 목표.
        target_weeks: 생성할 step 수. 현재는 1주차당 1개 step을 만든다.

    반환값:
        target_weeks 길이에 맞춘 step 제목 목록.

    현재 구현:
        goal에 "Django", "backend", "백엔드"가 포함되면 백엔드 학습 흐름을
        사용한다. 그 외 목표에는 범용 학습 흐름을 사용한다.

    향후 확장 지점:
        AI/RAG/Agent 기반 생성기가 들어오면 이 함수는 제거되거나 내부 구현만
        교체될 수 있다. 다만 generate_curriculum_plan이 반환하는 plan schema는
        저장 service가 기대하므로 유지하는 편이 안전하다.
    """
    lowered_goal = goal.lower()

    if "django" in lowered_goal or "backend" in lowered_goal or "백엔드" in goal:
        titles = [
            "Python 기초 복습",
            "웹과 백엔드 기본 개념 이해",
            "Django 프로젝트 구조 학습",
            "데이터베이스 모델링",
            "REST API 구현",
            "인증과 권한 처리",
            "배포 준비",
            "포트폴리오 프로젝트 완성",
        ]
    else:
        titles = [
            "학습 목표 구체화",
            "핵심 개념 학습",
            "기초 실습",
            "응용 실습",
            "작은 프로젝트 설계",
            "프로젝트 구현",
            "결과물 개선",
            "최종 정리",
        ]

    if target_weeks <= len(titles):
        return titles[:target_weeks]

    extra_titles = [
        f"{goal[:40]} 심화 학습 {index}"
        for index in range(1, target_weeks - len(titles) + 1)
    ]
    return titles + extra_titles


def generate_curriculum_plan(context):
    """
    정규화된 context를 받아 저장 가능한 커리큘럼 plan을 생성한다.

    입력값:
        context: build_curriculum_context가 만든 dict. 사용자 입력, 프로필
        fallback 값, goal 키워드, 관련 DB 후보 데이터가 들어 있다.

    반환값:
        curriculum_save_service가 기대하는 고정 schema의 dict.

        반환 schema:
            title: Curriculum.title에 저장할 제목.
            difficulty_level: 현재 커리큘럼 난이도. 임시 구현에서는 beginner.
            recommendation_reason: 사용자에게 보여줄 추천 이유.
            steps: CurriculumStep 및 연결 테이블 저장에 사용할 step 목록.

    현재 구현:
        AI를 호출하지 않는다. API, DB 모델, service 경계가 먼저 동작하도록
        deterministic rule-based 방식으로 DRAFT 커리큘럼을 만든다.

    향후 확장 지점:
        이 함수 내부가 RAG/Agent/LLM 기반 생성기로 교체될 예정이다. 교체 시에도
        save service가 사용하는 반환 schema를 유지하면 view와 저장 계층을 크게
        바꾸지 않아도 된다.
    """
    goal = context["goal"]
    target_weeks = context["target_weeks"]
    weekly_hours = context["weekly_available_hours"]
    style = context["preferred_learning_style"]
    topics = context["topics"]
    resources = context["resources"]
    courses = context["courses"]
    step_titles = build_step_titles(goal, target_weeks)

    steps = []
    for index, title in enumerate(step_titles, start=1):
        topic = topics[(index - 1) % len(topics)] if topics else None
        resource = resources[(index - 1) % len(resources)] if resources else None
        course = courses[(index - 1) % len(courses)] if courses else None

        steps.append(
            {
                "step_order": index,
                "title": title,
                "description": (
                    f"{index}주차에는 '{goal}' 목표를 위해 '{title}'을 학습합니다."
                ),
                "estimated_hours": weekly_hours,
                "difficulty_level": "beginner",
                "target_topic": topic,
                "prerequisite_note": "",
                "resources": [resource] if resource else [],
                "courses": [course] if course else [],
            }
        )

    return {
        "title": f"{goal[:80]} {target_weeks}주 커리큘럼",
        "difficulty_level": "beginner",
        "recommendation_reason": (
            f"학습 목표, 주간 {weekly_hours}시간의 학습 가능 시간, "
            f"'{style}' 선호 학습 방식을 기준으로 임시 커리큘럼을 생성했습니다."
        ),
        "steps": steps,
    }
