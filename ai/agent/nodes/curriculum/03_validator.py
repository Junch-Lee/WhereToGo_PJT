"""03_validator: LLM 출력의 식별자/slug 환각을 제거."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

FALLBACK_TOPIC_SLUG = "computer-science"
VALID_DIFFICULTIES = {"beginner", "intermediate", "advanced"}


def validate_curriculum(curriculum: dict, search_results: dict, topic_analysis: dict) -> dict:
    """Node 3 curriculum JSON을 저장 가능한 안전한 구조로 보정한다."""
    normalized = _normalize_curriculum_shape(curriculum)
    normalized = validate_identifiers(normalized, search_results)
    normalized = validate_topic_slugs(normalized, topic_analysis)
    normalized["steps"] = _normalize_step_order(normalized["steps"])
    return normalized


def validate_identifiers(curriculum: dict, search_results: dict) -> dict:
    """검색 결과에 없는 course/resource 식별자를 제거한다."""
    valid_courses = {
        _to_int(course.get("source_row_number"))
        for course in search_results.get("courses", [])
        if _to_int(course.get("source_row_number")) is not None
    }
    valid_resources = {
        _clean_text(resource.get("external_id"))
        for resource in search_results.get("resources", [])
        if _clean_text(resource.get("external_id"))
    }

    removed_courses = 0
    removed_resources = 0
    for step in curriculum.get("steps", []):
        original_courses = [_to_int(value) for value in step.get("course_source_row_numbers", [])]
        course_ids = _unique([value for value in original_courses if value in valid_courses])
        removed_courses += len([value for value in original_courses if value not in valid_courses])

        original_resources = [_clean_text(value) for value in step.get("resource_external_ids", [])]
        resource_ids = _unique([value for value in original_resources if value in valid_resources])
        removed_resources += len([value for value in original_resources if value not in valid_resources])

        step["course_source_row_numbers"] = course_ids
        step["resource_external_ids"] = resource_ids

    if removed_courses or removed_resources:
        logger.info(
            "Curriculum identifier validation removed courses=%s resources=%s",
            removed_courses,
            removed_resources,
        )
    return curriculum


def validate_topic_slugs(curriculum: dict, topic_analysis: dict) -> dict:
    """제공된 Topic 후보에 없는 target_topic_slug를 fallback으로 바꾼다."""
    valid_slugs = _valid_topic_slugs(topic_analysis)
    fallback_slug = FALLBACK_TOPIC_SLUG
    replacements = 0

    for step in curriculum.get("steps", []):
        slug = _clean_text(step.get("target_topic_slug"))
        if slug not in valid_slugs:
            step["target_topic_slug"] = fallback_slug
            replacements += 1

    if replacements:
        logger.info("Curriculum topic validation replaced invalid slugs=%s", replacements)
    return curriculum


def _normalize_curriculum_shape(curriculum: dict) -> dict:
    if not isinstance(curriculum, dict):
        raise TypeError("curriculum must be a dict.")

    difficulty = _clean_text(curriculum.get("difficulty_level")) or "beginner"
    if difficulty not in VALID_DIFFICULTIES:
        difficulty = "beginner"

    return {
        "title": _clean_text(curriculum.get("title")) or "개인 맞춤 커리큘럼",
        "difficulty_level": difficulty,
        "recommendation_reason": _clean_text(curriculum.get("recommendation_reason")),
        "steps": [_normalize_step(step) for step in curriculum.get("steps", []) if isinstance(step, dict)],
    }


def _normalize_step(step: dict) -> dict:
    difficulty = _clean_text(step.get("difficulty_level")) or "beginner"
    if difficulty not in VALID_DIFFICULTIES:
        difficulty = "beginner"

    return {
        "step_order": _to_int(step.get("step_order")) or 0,
        "title": _clean_text(step.get("title")) or "학습 단계",
        "description": _clean_text(step.get("description")),
        "target_topic_slug": _clean_text(step.get("target_topic_slug")),
        "difficulty_level": difficulty,
        "estimated_hours": max(_to_int(step.get("estimated_hours")) or 1, 1),
        "prerequisite_note": _clean_text(step.get("prerequisite_note")),
        "course_source_row_numbers": list(step.get("course_source_row_numbers") or []),
        "resource_external_ids": list(step.get("resource_external_ids") or []),
    }


def _normalize_step_order(steps: list[dict]) -> list[dict]:
    for index, step in enumerate(steps, start=1):
        step["step_order"] = index
    return steps


def _valid_topic_slugs(topic_analysis: dict) -> set[str]:
    slugs = {FALLBACK_TOPIC_SLUG}
    for key in ("target_topics", "context_topics", "prerequisite_candidates"):
        for topic in topic_analysis.get(key, []) or []:
            slug = _clean_text(topic.get("slug"))
            if slug:
                slugs.add(slug)
    return slugs


def _unique(values: list[Any]) -> list[Any]:
    seen: set[Any] = set()
    result: list[Any] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _clean_text(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _to_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

