"""01_prompt_builder: Node 1/2 결과로 커리큘럼 생성 프롬프트 구성."""

from __future__ import annotations

from typing import Any
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.chat_completion import ChatCompletion

import json


def build_curriculum_prompt(
    user_profile: dict,
    topic_analysis: dict,
    search_results: dict,
) -> list[ChatCompletionMessageParam]:
    
    """LLM에 전달할 system/user messages를 만든다."""
    payload = {
        "user_profile": _compact_user_profile(user_profile),
        "topic_analysis": _compact_topic_analysis(topic_analysis),
        "search_results": _compact_search_results(search_results),
        "step_count_guide": _step_count_guide(_to_int(user_profile.get("target_weeks"), 8)),
        "total_available_hours": _total_hours(user_profile),
        "output_schema": _output_schema(),
        "rules": [
            "Return only a JSON object.",
            "Prefer Korean for user-facing text fields: title, recommendation_reason, step title, step description, and prerequisite_note.",
            "Use only course_source_row_numbers present in search_results.courses.",
            "Use only resource_external_ids present in search_results.resources.",
            "When search results are available, every step should reference at least one relevant course_source_row_number or resource_external_id.",
            "When beginner resources are available, use at least one relevant resource_external_id in the first step.",
            "Choose one target_topic_slug per step from the provided topic slugs.",
            "If no specific topic fits, use computer-science.",
            "Do not include Django model objects or database IDs.",
        ],
    }
    return [
        {
            "role": "system",
            "content": (
                "You generate practical computer-science learning curricula. "
                "You must return valid JSON only."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(payload, ensure_ascii=False),
        },
    ]


def _compact_user_profile(user_profile: dict) -> dict:
    return {
        "goal": _clean_text(user_profile.get("goal")),
        "purpose": _clean_text(user_profile.get("purpose")),
        "difficulty_level": _clean_text(user_profile.get("difficulty_level")) or "beginner",
        "target_weeks": _to_int(user_profile.get("target_weeks"), 8),
        "weekly_available_hours": _to_int(user_profile.get("weekly_available_hours"), 7),
        "preferred_learning_style": _clean_text(user_profile.get("preferred_learning_style")) or "balanced",
    }


def _compact_topic_analysis(topic_analysis: dict) -> dict:
    return {
        "target_topics": _compact_topics(topic_analysis.get("target_topics") or []),
        "context_topics": _compact_topics(topic_analysis.get("context_topics") or []),
        "prerequisite_candidates": _compact_topics(topic_analysis.get("prerequisite_candidates") or []),
    }


def _compact_topics(topics: list[dict]) -> list[dict]:
    compacted: list[dict] = []
    for topic in topics:
        slug = _clean_text(topic.get("slug"))
        if not slug:
            continue
        compacted.append(
            {
                "slug": slug,
                "name": _clean_text(topic.get("name")),
            }
        )
    return compacted


def _compact_search_results(search_results: dict) -> dict:
    return {
        "courses": [
            {
                "source_row_number": course.get("source_row_number"),
                "course_name": _clean_text(course.get("course_name")),
                "score": course.get("score", 0),
                "topic_names": _clean_text((course.get("metadata") or {}).get("topic_names")),
                "estimated_difficulty": _clean_text((course.get("metadata") or {}).get("estimated_difficulty")),
                "grade": (course.get("metadata") or {}).get("grade"),
            }
            for course in search_results.get("courses", [])
        ],
        "resources": [
            {
                "external_id": _clean_text(resource.get("external_id")),
                "title": _clean_text(resource.get("title")),
                "score": resource.get("score", 0),
                "topic_names": _clean_text((resource.get("metadata") or {}).get("topic_names")),
                "difficulty_level": _clean_text((resource.get("metadata") or {}).get("difficulty_level")),
                "content_type": _clean_text((resource.get("metadata") or {}).get("content_type")),
            }
            for resource in search_results.get("resources", [])
        ],
    }


def _step_count_guide(target_weeks: int) -> str:
    if target_weeks <= 4:
        return "3-4 steps"
    if target_weeks <= 8:
        return "4-5 steps"
    if target_weeks <= 16:
        return "5-7 steps"
    return "6-8 steps"


def _total_hours(user_profile: dict) -> int:
    return _to_int(user_profile.get("target_weeks"), 8) * _to_int(
        user_profile.get("weekly_available_hours"),
        7,
    )


def _output_schema() -> dict:
    return {
        "title": "str",
        "difficulty_level": "beginner|intermediate|advanced",
        "recommendation_reason": "str",
        "steps": [
            {
                "step_order": "int",
                "title": "str",
                "description": "str",
                "target_topic_slug": "str",
                "difficulty_level": "beginner|intermediate|advanced",
                "estimated_hours": "int",
                "prerequisite_note": "str",
                "course_source_row_numbers": ["int"],
                "resource_external_ids": ["str"],
            }
        ],
    }


def _clean_text(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
