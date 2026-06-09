"""Shared state shape for the LangGraph agent."""

from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    """
    LangGraph node state 정의 영역.
    TypeDict 남용 시 발생하는 오류를 줄이기 위해 AgentState의 최상단 영역만 TypedDict(StateNode 권장 사항)로 유지
    """

    raw_input: dict
    user_profile: dict
    topic_analysis: dict
    search_query: str
    is_in_scope: bool
    search_results: dict
    curriculum: dict

