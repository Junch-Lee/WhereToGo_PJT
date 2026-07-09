"""Rule-based Topic Catalog matching for Node 1.

topic_catalog : 주입받은 Topic Catalog에서 name/alias 기반 1차 후보 매칭 및 저장
- Rule-Based + LLM assist 형식
"""

from __future__ import annotations

import re
from typing import Iterable


def match_candidates(goal_text: str, catalog: list[dict]) -> list[dict]:
    """Return topic candidates whose name or alias appears in goal_text."""
    normalized_goal = _normalize_text(goal_text)
    if not normalized_goal:
        return []

    candidates: list[dict] = []
    seen_slugs: set[str] = set()

    for topic in catalog:
        slug = str(topic.get("slug") or "").strip()
        if not slug or slug in seen_slugs:
            continue

        matched_term = _find_matching_term(normalized_goal, _topic_terms(topic))
        if not matched_term:
            continue

        seen_slugs.add(slug)
        candidates.append(
            {
                "slug": slug,
                "name": str(topic.get("name") or slug),
                "depth": _as_int(topic.get("depth")),
                "parent_slug": topic.get("parent_slug"),
                "topic_type": topic.get("topic_type"),
                "is_learning_unit": bool(topic.get("is_learning_unit", False)),
                "is_assessable": bool(topic.get("is_assessable", False)),
                "aliases": list(topic.get("aliases") or []),
                "confidence": _rule_confidence(matched_term, topic),
                "match_reason": f"Matched topic term: {matched_term}",
            }
        )

    return sorted(candidates, key=lambda item: (-float(item["confidence"]), item["depth"], item["slug"]))


def expand_context(candidates: list[dict], catalog: list[dict]) -> list[dict]:
    """Add parent topics as context candidates without promoting them to targets."""
    by_slug = {topic.get("slug"): topic for topic in catalog if topic.get("slug")}
    context: list[dict] = []
    seen_slugs: set[str] = set()

    for candidate in candidates:
        parent_slug = candidate.get("parent_slug")
        while parent_slug and parent_slug not in seen_slugs:
            parent = by_slug.get(parent_slug)
            if not parent:
                break
            seen_slugs.add(parent_slug)
            context.append(
                {
                    "slug": parent_slug,
                    "name": str(parent.get("name") or parent_slug),
                    "depth": _as_int(parent.get("depth")),
                    "reason": f"Parent topic of {candidate.get('slug')}",
                }
            )
            parent_slug = parent.get("parent_slug")

    return context


def extract_unmatched_terms(goal_text: str, candidates: list[dict]) -> list[str]:
    """Return coarse unmatched Korean/English terms after removing matched terms."""
    remaining = _normalize_text(goal_text)
    for candidate in candidates:
        terms = [candidate.get("name", ""), *candidate.get("aliases", [])]
        for term in terms:
            normalized_term = _normalize_text(str(term))
            if normalized_term:
                remaining = remaining.replace(normalized_term, " ")

    stopwords = {
        "배우고",
        "싶고",
        "싶어요",
        "싶어",
        "보완",
        "보완하고",
        "잘하고",
        "학습",
        "공부",
        "입문",
        "기초",
        "취업",
        "이직",
        "위해",
        "하고",
        "싶다",
        "learn",
        "study",
        "for",
        "and",
    }
    terms = re.findall(r"[0-9a-zA-Z가-힣+#.]+", remaining)
    normalized_terms = [_strip_korean_suffixes(term) for term in terms]
    return [
        term
        for term in normalized_terms
        if len(term) > 1 and term.lower() not in stopwords
    ]


def _topic_terms(topic: dict) -> Iterable[str]:
    yield str(topic.get("name") or "")
    for alias in topic.get("aliases") or []:
        yield str(alias)


def _find_matching_term(normalized_goal: str, terms: Iterable[str]) -> str | None:
    best_term = ""
    for term in terms:
        normalized_term = _normalize_text(term)
        if normalized_term and normalized_term in normalized_goal and len(normalized_term) > len(best_term):
            best_term = normalized_term
    return best_term or None


def _rule_confidence(matched_term: str, topic: dict) -> float:
    normalized_name = _normalize_text(str(topic.get("name") or ""))
    if matched_term == normalized_name:
        return 0.9
    return 0.82


def _normalize_text(value: str) -> str:
    lowered = str(value or "").lower()
    return re.sub(r"\s+", " ", lowered).strip()


def _strip_korean_suffixes(term: str) -> str:
    """Remove common short Korean particles/endings from rough unmatched terms."""
    suffixes = (
        "으로",
        "하고",
        "도",
        "은",
        "는",
        "이",
        "가",
        "을",
        "를",
        "과",
        "와",
    )
    for suffix in suffixes:
        if term.endswith(suffix) and len(term) > len(suffix) + 1:
            return term[: -len(suffix)]
    return term


def _as_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
