"""AI Agent 결과를 백엔드 계약 응답으로 정규화하는 service."""

ALLOWED_STATUSES = {"success", "out_of_scope", "needs_clarification", "no_results"}

GENERATION_STATUS_MAP = {
    "generated": "success",
    "out_of_scope": "out_of_scope",
    "insufficient_search_results": "no_results",
}


def normalize_agent_response(agent_result: dict) -> dict:
    """AI Agent 내부 결과 dict를 백엔드 guide 기준 schema로 변환한다.

    이 함수가 필요한 이유:
        현재 AI Agent는 graph/node 내부 상태를 나타내는 ``generation_status`` 중심의
        AgentState를 반환한다. 반면 백엔드 API와 저장 service는 사용자 응답과 저장
        분기를 위해 ``success``, ``out_of_scope``, ``needs_clarification``,
        ``no_results`` 네 가지 status 계약을 기준으로 동작해야 한다. 이 service는
        두 계약 사이의 얇은 변환 계층이다.

    AI 내부 status와 백엔드 API status를 분리하는 이유:
        AI graph의 status는 node routing과 디버깅에 가까운 내부 상태이고, 백엔드
        status는 View/API 응답과 저장 여부를 결정하는 외부 계약이다. 둘을 분리해야
        AI graph 구조가 바뀌어도 API 계약 변경 범위를 이 함수로 제한할 수 있다.

    DB 저장을 하지 않는 이유:
        AI는 DB 객체가 아니라 ``target_topic_slug``, ``course_source_row_numbers``,
        ``resource_external_ids`` 같은 식별자만 반환한다. 이 함수는 식별자를 보존만
        하고, 실제 FK 조회와 Curriculum 저장은 다음 단계의 저장 service가 담당한다.

    Args:
        agent_result: ``ai.agent.run_agent()`` 호출이 끝난 뒤 받은 AgentState dict.

    Returns:
        백엔드 guide 기준으로 정규화된 dict. 반환 dict에는 항상 ``status``가 포함된다.

    Raises:
        ValueError: 알 수 없는 ``generation_status``가 들어온 경우. 이 경우는 자료 부족
            같은 정상 분기가 아니라 AI-백엔드 계약 불일치에 가깝기 때문에 조용히
            ``no_results``로 숨기지 않는다.
    """
    if not isinstance(agent_result, dict):
        raise TypeError("agent_result must be a dict.")

    status = _resolve_backend_status(agent_result)
    if status == "success":
        return _normalize_success(agent_result)
    if status == "needs_clarification":
        return _normalize_needs_clarification(agent_result)
    return _normalize_message_branch(status, agent_result)


def _resolve_backend_status(agent_result: dict) -> str:
    generation_status = _clean_text(agent_result.get("generation_status"))

    # out_of_scope는 graph가 명시적으로 종료한 상태이므로 topic_analysis의
    # needs_clarification 값보다 우선한다. 현재 AI 분석기는 out-of-scope에도
    # clarification 질문을 담을 수 있기 때문이다.
    if generation_status:
        try:
            return GENERATION_STATUS_MAP[generation_status]
        except KeyError as exc:
            raise ValueError(f"Unknown AI generation_status: {generation_status}") from exc

    topic_analysis = agent_result.get("topic_analysis") or {}
    if topic_analysis.get("needs_clarification"):
        return "needs_clarification"

    raise ValueError("agent_result does not include generation_status.")


def _normalize_success(agent_result: dict) -> dict:
    curriculum = agent_result.get("curriculum") or {}
    user_profile = agent_result.get("user_profile") or {}
    return {
        "status": "success",
        "title": _clean_text(curriculum.get("title")),
        "recommendation_reason": _clean_text(curriculum.get("recommendation_reason")),
        "user_profile": dict(user_profile),
        "steps": [_normalize_step(step) for step in curriculum.get("steps", [])],
    }


def _normalize_step(step: dict) -> dict:
    # 저장 service가 다음 PR에서 식별자를 FK로 변환해야 하므로 identifier 필드는
    # 이름과 타입을 바꾸지 않고 그대로 보존한다.
    return {
        "order": step.get("step_order"),
        "title": _clean_text(step.get("title")),
        "description": _clean_text(step.get("description")),
        "target_topic_slug": _clean_text(step.get("target_topic_slug")),
        "difficulty_level": _clean_text(step.get("difficulty_level")),
        "estimated_hours": step.get("estimated_hours"),
        "prerequisite_note": _clean_text(step.get("prerequisite_note")),
        "course_source_row_numbers": list(step.get("course_source_row_numbers") or []),
        "resource_external_ids": list(step.get("resource_external_ids") or []),
    }


def _normalize_needs_clarification(agent_result: dict) -> dict:
    topic_analysis = agent_result.get("topic_analysis") or {}
    return {
        "status": "needs_clarification",
        "clarification_question": _clean_text(topic_analysis.get("clarification_question")),
    }


def _normalize_message_branch(status: str, agent_result: dict) -> dict:
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"Unknown backend status: {status}")

    topic_analysis = agent_result.get("topic_analysis") or {}
    return {
        "status": status,
        "message": _clean_text(agent_result.get("message"))
        or _clean_text(topic_analysis.get("clarification_question")),
    }


def _clean_text(value: object) -> str:
    return str(value).strip() if value is not None else ""
