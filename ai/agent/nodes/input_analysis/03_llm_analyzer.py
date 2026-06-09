"""
llm_analyzer : 후보 Topic만 LLM에 전달, JSON 결과를 강제 보정,  실패 시 rule fallback(우아한 실패)
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import re
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)
AI_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"

COMPUTER_SCIENCE_KEYWORDS = (
    "ai",
    "algorithm",
    "backend",
    "computer",
    "data",
    "database",
    "deep learning",
    "frontend",
    "machine learning",
    "network",
    "programming",
    "python",
    "software",
    "web",
    "개발",
    "네트워크",
    "데이터",
    "딥러닝",
    "머신러닝",
    "백엔드",
    "소프트웨어",
    "알고리즘",
    "인공지능",
    "자료구조",
    "컴퓨터",
    "프론트엔드",
)

OUT_OF_SCOPE_KEYWORDS = (
    "영어",
    "회화",
    "토익",
    "요리",
    "운동",
    "피아노",
    "미술",
    "일본어",
    "중국어",
)

MATH_PREREQUISITE_SLUGS = {
    "mathematics-for-cs",
    "linear-algebra",
    "probability-statistics",
    "calculus",
}
MATH_HEAVY_TARGET_SLUGS = {
    "machine-learning",
    "deep-learning",
}


def analyze_with_llm(
    goal_text: str,
    purpose: str,
    candidates: list[dict],
    context_candidates: list[dict],
) -> dict:
    """Classify candidate topics and create the Node 2 search query.

    Falls back to deterministic rules when credentials are missing, the API call
    fails, or the response is not valid JSON.
    """
    fallback = _fallback_analysis(goal_text, purpose, candidates, context_candidates)
    if not _has_gms_key():
        return fallback

    try:
        from ai.core.config import settings

        client = OpenAI(api_key=settings.gms_key, base_url=settings.openai_base_url)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _system_prompt()},
                {"role": "user", "content": _user_prompt(goal_text, purpose, candidates, context_candidates)},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or ""
        parsed = _parse_json_object(content)
        return _sanitize_analysis(_merge_with_fallback(parsed, fallback), fallback)
    except Exception as exc:  # pragma: no cover - network/config dependent
        logger.warning("LLM analysis failed; using rule fallback. error=%s", exc)
        return fallback


def _fallback_analysis(
    goal_text: str,
    purpose: str,
    candidates: list[dict],
    context_candidates: list[dict],
) -> dict:
    text = f"{goal_text} {purpose}".lower()
    has_cs_signal = bool(candidates) or any(keyword in text for keyword in COMPUTER_SCIENCE_KEYWORDS)
    has_out_signal = any(keyword in text for keyword in OUT_OF_SCOPE_KEYWORDS)
    is_in_scope = has_cs_signal and not (has_out_signal and not has_cs_signal)
    needs_clarification = is_in_scope and not candidates

    target_topics = [_target_topic(candidate) for candidate in candidates]
    prerequisite_topics = _split_prerequisite_topics(target_topics)
    if prerequisite_topics:
        prerequisite_slugs = {topic["slug"] for topic in prerequisite_topics}
        target_topics = [topic for topic in target_topics if topic.get("slug") not in prerequisite_slugs]

    context_topics = [_context_topic(candidate) for candidate in context_candidates]

    if not is_in_scope:
        question = "현재는 컴퓨터공학 분야 커리큘럼만 제공합니다. 컴퓨터공학 관련 학습 목표를 입력해 주세요."
    elif needs_clarification:
        question = "어떤 컴퓨터공학 주제를 중심으로 배우고 싶은지 조금 더 구체적으로 알려주세요."
    else:
        question = ""

    return {
        "original_input": goal_text,
        "is_in_scope": is_in_scope,
        "search_query": _build_search_query(goal_text, purpose, target_topics, context_topics),
        "target_topics": target_topics,
        "context_topics": context_topics,
        "prerequisite_candidates": prerequisite_topics,
        "unmatched_terms": [],
        "needs_clarification": needs_clarification or not is_in_scope,
        "clarification_question": question,
    }


def _has_gms_key() -> bool:
    load_dotenv(dotenv_path=AI_ENV_FILE)
    load_dotenv()
    return bool(os.getenv("GMS_KEY"))


def _split_prerequisite_topics(target_topics: list[dict]) -> list[dict]:
    target_slugs = {topic.get("slug") for topic in target_topics}
    if not target_slugs.intersection(MATH_HEAVY_TARGET_SLUGS):
        return []

    prerequisites: list[dict] = []
    for topic in target_topics:
        if topic.get("slug") in MATH_PREREQUISITE_SLUGS:
            prerequisites.append(
                {
                    "slug": topic.get("slug"),
                    "name": topic.get("name"),
                    "reason": "Machine learning goals commonly need this math foundation.",
                }
            )
    return prerequisites


def _target_topic(candidate: dict) -> dict:
    return {
        "slug": candidate.get("slug"),
        "name": candidate.get("name"),
        "depth": candidate.get("depth", 0),
        "confidence": float(candidate.get("confidence", 0.75)),
        "match_reason": candidate.get("match_reason", "Rule-based topic match"),
    }


def _context_topic(candidate: dict) -> dict:
    return {
        "slug": candidate.get("slug"),
        "name": candidate.get("name"),
        "depth": candidate.get("depth", 0),
        "reason": candidate.get("reason", "Context topic"),
    }


def _build_search_query(
    goal_text: str,
    purpose: str,
    target_topics: list[dict],
    context_topics: list[dict],
) -> str:
    topic_names = [str(topic.get("name")) for topic in [*target_topics, *context_topics] if topic.get("name")]
    parts = [goal_text.strip(), purpose.strip(), *topic_names]
    query = " ".join(part for part in parts if part).strip()
    return re.sub(r"\s+", " ", query)


def _merge_with_fallback(parsed: dict, fallback: dict) -> dict:
    merged = dict(fallback)
    for key in (
        "original_input",
        "is_in_scope",
        "search_query",
        "target_topics",
        "context_topics",
        "prerequisite_candidates",
        "unmatched_terms",
        "needs_clarification",
        "clarification_question",
    ):
        if key in parsed and parsed[key] is not None:
            merged[key] = parsed[key]
    return merged


def _sanitize_analysis(analysis: dict, fallback: dict) -> dict:
    """Keep the LLM result inside the Node 1 output contract."""
    sanitized = dict(analysis)

    if fallback.get("is_in_scope") and fallback.get("needs_clarification"):
        sanitized["is_in_scope"] = True
        sanitized["needs_clarification"] = True

    if not sanitized.get("is_in_scope"):
        sanitized["needs_clarification"] = True
        if not sanitized.get("clarification_question"):
            sanitized["clarification_question"] = fallback.get("clarification_question", "")

    fallback_targets = {topic.get("slug"): topic for topic in fallback.get("target_topics", [])}
    sanitized["target_topics"] = [
        _complete_topic(topic, fallback_targets.get(topic.get("slug")), is_target=True)
        for topic in sanitized.get("target_topics", [])
        if isinstance(topic, dict)
    ]

    fallback_context = {topic.get("slug"): topic for topic in fallback.get("context_topics", [])}
    sanitized["context_topics"] = [
        _complete_topic(topic, fallback_context.get(topic.get("slug")), is_target=False)
        for topic in sanitized.get("context_topics", [])
        if isinstance(topic, dict)
    ]

    sanitized["prerequisite_candidates"] = [
        {
            "slug": topic.get("slug"),
            "name": topic.get("name"),
            "reason": topic.get("reason", ""),
        }
        for topic in sanitized.get("prerequisite_candidates", [])
        if isinstance(topic, dict)
    ]
    return sanitized


def _complete_topic(topic: dict, fallback_topic: dict | None, is_target: bool) -> dict:
    source = fallback_topic or {}
    completed = {
        "slug": topic.get("slug") or source.get("slug"),
        "name": topic.get("name") or source.get("name"),
        "depth": topic.get("depth", source.get("depth", 0)),
    }
    if is_target:
        completed["confidence"] = float(topic.get("confidence", source.get("confidence", 0.75)))
        completed["match_reason"] = topic.get("match_reason") or source.get("match_reason", "")
    else:
        completed["reason"] = topic.get("reason") or source.get("reason", "")
    return completed


def _parse_json_object(content: str) -> dict:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("LLM response must be a JSON object.")
    return parsed


def _system_prompt() -> str:
    return (
        "You classify a user's curriculum goal for a computer science education agent. "
        "Return only JSON. Use only the candidate topics provided by slug. "
        "Do not invent topic slugs."
    )


def _user_prompt(
    goal_text: str,
    purpose: str,
    candidates: list[dict],
    context_candidates: list[dict],
) -> str:
    payload: dict[str, Any] = {
        "goal_text": goal_text,
        "purpose": purpose,
        "candidate_topics": [_llm_topic(candidate) for candidate in candidates],
        "context_topics": [_llm_topic(candidate) for candidate in context_candidates],
        "required_json_keys": [
            "original_input",
            "is_in_scope",
            "search_query",
            "target_topics",
            "context_topics",
            "prerequisite_candidates",
            "unmatched_terms",
            "needs_clarification",
            "clarification_question",
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def _llm_topic(topic: dict) -> dict:
    return {
        "slug": topic.get("slug"),
        "name": topic.get("name"),
        "depth": topic.get("depth"),
        "parent_slug": topic.get("parent_slug"),
        "aliases": topic.get("aliases", []),
    }
