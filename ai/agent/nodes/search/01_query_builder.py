"""01_query_builder: Node 1 결과를 RAG 검색 입력으로 변환."""

from __future__ import annotations

VALID_DIFFICULTIES = {"beginner", "intermediate", "advanced"}


def build_search_query(search_query: str, topic_analysis: dict) -> str:
    """기본 검색어에 target/prerequisite Topic 이름을 결합한다."""
    parts = [_clean_text(search_query)]

    for topic in topic_analysis.get("target_topics") or []:
        _append_topic_name(parts, topic)
    for topic in topic_analysis.get("prerequisite_candidates") or []:
        _append_topic_name(parts, topic)

    query = " ".join(part for part in parts if part)
    if not query:
        raise ValueError("search_query must not be empty.")
    return query


def build_resource_filter(user_profile: dict) -> dict | None:
    """사용자 난이도에 맞는 resources 필터를 만든다."""
    difficulty = _clean_text(user_profile.get("difficulty_level")).lower()
    if difficulty not in VALID_DIFFICULTIES:
        return None
    return {"difficulty_level": difficulty}


def _append_topic_name(parts: list[str], topic: dict) -> None:
    name = _clean_text(topic.get("name"))
    if not name:
        return
    if any(name in part for part in parts):
        return
    parts.append(name)


def _clean_text(value: object) -> str:
    return str(value).strip() if value is not None else ""

