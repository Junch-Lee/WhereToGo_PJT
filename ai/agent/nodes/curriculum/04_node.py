"""04_node: Node 3 커리큘럼 생성 오케스트레이션."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
import logging
from typing import Any, cast

CurriculumGenerator = Callable[[list[dict[str, Any]]], dict[str, Any]]
PromptBuilder = Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], list[dict[str, Any]]]
CurriculumValidator = Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], dict[str, Any]]

_prompt_builder = import_module("ai.agent.nodes.curriculum.01_prompt_builder")
_llm_generator = import_module("ai.agent.nodes.curriculum.02_llm_generator")
_validator = import_module("ai.agent.nodes.curriculum.03_validator")

build_curriculum_prompt = cast(PromptBuilder, _prompt_builder.build_curriculum_prompt)
generate_curriculum = cast(CurriculumGenerator, _llm_generator.generate_curriculum)
validate_curriculum = cast(CurriculumValidator, _validator.validate_curriculum)

logger = logging.getLogger(__name__)


def run_curriculum_generation(
    state: dict[str, Any],
    generator_fn: CurriculumGenerator | None = None,
) -> dict[str, Any]:
    """State의 Node 1/2 결과로 curriculum JSON을 생성한다."""
    if not state.get("is_in_scope", False):
        return _skip("out_of_scope", "현재는 컴퓨터공학 분야 커리큘럼만 생성할 수 있습니다.")

    user_profile = state.get("user_profile") or {}
    topic_analysis = state.get("topic_analysis") or {}
    search_results = state.get("search_results") or {}

    if not _has_search_results(search_results):
        return _skip("insufficient_search_results", "커리큘럼 생성에 필요한 검색 결과가 부족합니다.")

    messages = build_curriculum_prompt(user_profile, topic_analysis, search_results)
    curriculum_generator = generator_fn if generator_fn is not None else generate_curriculum
    raw_curriculum = curriculum_generator(messages)
    curriculum = validate_curriculum(raw_curriculum, search_results, topic_analysis)

    logger.info("Curriculum generated: steps=%s title=%s", len(curriculum["steps"]), curriculum["title"])
    return {
        "curriculum": curriculum,
        "generation_status": "generated",
        "message": "",
    }


def _has_search_results(search_results: dict) -> bool:
    return bool(search_results.get("courses") or search_results.get("resources"))


def _skip(status: str, message: str) -> dict:
    logger.info("Curriculum generation skipped: %s", status)
    return {
        "curriculum": None,
        "generation_status": status,
        "message": message,
    }
