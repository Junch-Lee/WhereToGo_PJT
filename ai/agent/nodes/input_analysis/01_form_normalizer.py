"""
1. 사용자 입력 폼 정규화 :

Q1 ~ Q7 입력을 goal, target_weeks, weekly_available_hours, difficulty_level 등 
Curriculum 모델 친화 필드로 정규화
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_TARGET_WEEKS = 8
DEFAULT_WEEKLY_HOURS = 7
DEFAULT_DIFFICULTY = "beginner"
DEFAULT_LEARNING_STYLE = "balanced"


def normalize_form(raw_input: dict) -> dict:
    """Map raw Q1-Q7 form answers to curriculum-friendly profile fields."""
    if not isinstance(raw_input, dict):
        raise TypeError("raw_input must be a dict.")

    goal = _clean_text(raw_input.get("goal_text") or raw_input.get("goal") or "")
    purpose = _clean_text(raw_input.get("purpose") or "")

    if not goal:
        logger.warning("Input analysis received an empty goal_text.")

    return {
        "goal": goal,
        "purpose": purpose,
        "difficulty_level": _normalize_level(raw_input.get("level")),
        "target_weeks": _normalize_period(raw_input.get("period")),
        "weekly_available_hours": _normalize_weekly_hours(raw_input.get("weekly_hours")),
        "preferred_learning_style": _normalize_learning_style(raw_input.get("learning_style")),
    }


def _normalize_level(value: Any) -> str:
    text = _normalize_key(value)
    if not text:
        return DEFAULT_DIFFICULTY
    if any(token in text for token in ("complete beginner", "beginner", "입문", "초보")):
        return "beginner"
    if any(token in text for token in ("advanced", "심화", "실무", "경험")):
        return "advanced"
    if any(token in text for token in ("intermediate", "기초", "있음", "중급")):
        return "intermediate"
    return DEFAULT_DIFFICULTY


def _normalize_period(value: Any) -> int:
    text = _normalize_key(value)
    if not text:
        return DEFAULT_TARGET_WEEKS
    if "2주" in text or "2week" in text:
        return 2
    if "1~2" in text or "1-2" in text or "1개월" in text or "2개월" in text:
        return 8
    if "3~4" in text or "3-4" in text or "3개월" in text or "4개월" in text:
        return 16
    if "4개월+" in text or "4개월이상" in text or "4개월 이상" in text:
        return 24
    if "정하지" in text or "미정" in text:
        return DEFAULT_TARGET_WEEKS
    return DEFAULT_TARGET_WEEKS


def _normalize_weekly_hours(value: Any) -> int:
    text = _normalize_key(value)
    if not text:
        return DEFAULT_WEEKLY_HOURS
    if "10~15" in text or "10-15" in text:
        return 12
    if "20h+" in text or "20+" in text or "20시간" in text:
        return 20
    if "~5" in text or "5h" in text or "5시간" in text:
        return 5
    if "7h" in text or "7시간" in text:
        return 7

    numbers = [int(match) for match in re.findall(r"\d+", text)]
    if not numbers:
        return DEFAULT_WEEKLY_HOURS
    if len(numbers) >= 2:
        return round(sum(numbers[:2]) / 2)
    return numbers[0]


def _normalize_learning_style(value: Any) -> str:
    text = _normalize_key(value)
    if not text:
        return DEFAULT_LEARNING_STYLE
    if any(token in text for token in ("lecture", "강의")):
        return "lecture"
    if any(token in text for token in ("project", "프로젝트", "실습")):
        return "project"
    if any(token in text for token in ("balanced", "균형", "상관없")):
        return "balanced"
    return DEFAULT_LEARNING_STYLE


def _clean_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _normalize_key(value: Any) -> str:
    return re.sub(r"\s+", "", _clean_text(value).lower())
