"""Smoke test Node 1, Node 2, and Node 3 with real OpenAI API calls.

Run from bash:
    python ai/verify/08_verify_agent_nodes_openai.py

Prerequisites:
    export GMS_KEY="sk-..."
    export OPENAI_BASE_URL="https://api.openai.com/v1"
    export OPENAI_CHAT_MODEL="gpt-4o-mini"
    python -m ai.indexing.indexer --target all --reset
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.agent.nodes.curriculum import run_curriculum_generation  # noqa: E402
from ai.agent.nodes.input_analysis import SAMPLE_TOPIC_CATALOG, run_input_analysis  # noqa: E402
from ai.agent.nodes.search import run_search  # noqa: E402
from ai.core.config import settings  # noqa: E402


RAW_INPUT = {
    "goal_text": "머신러닝을 배우고 싶고, 필요한 수학 기초도 함께 보완하고 싶어요.",
    "purpose": "취업/이직",
    "level": "완전 입문",
    "period": "3~4개월",
    "weekly_hours": "10~15시간",
    "learning_style": "프로젝트 중심",
    "concern": "",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify agent nodes with real OpenAI calls.")
    parser.add_argument("--json", action="store_true", help="Print full JSON outputs.")
    args = parser.parse_args()

    if not settings.gms_key:
        raise RuntimeError("GMS_KEY is required. Set it with: export GMS_KEY='sk-...'")

    print("## Node 1: input analysis")
    node1_result = run_input_analysis(RAW_INPUT, SAMPLE_TOPIC_CATALOG)
    _assert_node1_result(node1_result)
    _print_summary(
        {
            "is_in_scope": node1_result["is_in_scope"],
            "search_query": node1_result["search_query"],
            "target_topics": _topic_slugs(node1_result["topic_analysis"]["target_topics"]),
            "prerequisites": _topic_slugs(node1_result["topic_analysis"]["prerequisite_candidates"]),
        }
    )
    _print_full_json(node1_result, args.json)

    print("\n## Node 2: RAG search")
    node2_result = run_search(node1_result)
    _assert_node2_result(node2_result)
    search_results = node2_result["search_results"]
    _print_summary(
        {
            "query": search_results["query"],
            "course_count": len(search_results["courses"]),
            "resource_count": len(search_results["resources"]),
            "top_course": _first_value(search_results["courses"], "course_name"),
            "top_resource": _first_value(search_results["resources"], "title"),
        }
    )
    _print_full_json(node2_result, args.json)

    print("\n## Node 3: curriculum generation")
    node3_state = {**node1_result, **node2_result}
    node3_result = run_curriculum_generation(node3_state)
    _assert_node3_result(node3_result, search_results)
    curriculum = node3_result["curriculum"]
    _print_summary(
        {
            "generation_status": node3_result["generation_status"],
            "title": curriculum["title"],
            "difficulty_level": curriculum["difficulty_level"],
            "step_count": len(curriculum["steps"]),
            "first_step": _first_value(curriculum["steps"], "title"),
        }
    )
    _print_full_json(node3_result, args.json)

    print("\nOK: Node 1, Node 2, and Node 3 completed with real API-backed calls.")


def _assert_node1_result(result: dict[str, Any]) -> None:
    if not result.get("is_in_scope"):
        raise AssertionError("Node 1 should classify the sample machine-learning goal as in scope.")
    if not result.get("search_query"):
        raise AssertionError("Node 1 must produce a non-empty search_query.")

    topic_analysis = result.get("topic_analysis") or {}
    target_topics = topic_analysis.get("target_topics") or []
    if not target_topics:
        raise AssertionError("Node 1 must produce at least one target topic.")


def _assert_node2_result(result: dict[str, Any]) -> None:
    search_results = result.get("search_results") or {}
    courses = search_results.get("courses") or []
    resources = search_results.get("resources") or []
    if not courses and not resources:
        raise AssertionError(
            "Node 2 returned no search results. Run: python -m ai.indexing.indexer --target all --reset"
        )

    for course in courses:
        if course.get("source_row_number") is None:
            raise AssertionError("Every course result must include source_row_number.")
        if not isinstance(course.get("score"), int | float):
            raise AssertionError("Every course result must include a numeric score.")

    for resource in resources:
        if not resource.get("external_id"):
            raise AssertionError("Every resource result must include external_id.")
        if not isinstance(resource.get("score"), int | float):
            raise AssertionError("Every resource result must include a numeric score.")


def _assert_node3_result(result: dict[str, Any], search_results: dict[str, Any]) -> None:
    if result.get("generation_status") != "generated":
        raise AssertionError("Node 3 generation_status must be generated.")

    curriculum = result.get("curriculum") or {}
    steps = curriculum.get("steps") or []
    if not curriculum.get("title"):
        raise AssertionError("Node 3 curriculum must include title.")
    if len(steps) < 3:
        raise AssertionError("Node 3 curriculum should include at least three steps.")

    valid_courses = {course.get("source_row_number") for course in search_results.get("courses", [])}
    valid_resources = {resource.get("external_id") for resource in search_results.get("resources", [])}
    has_search_references = bool(valid_courses or valid_resources)

    for index, step in enumerate(steps, start=1):
        if step.get("step_order") != index:
            raise AssertionError("Node 3 step_order must be normalized from 1.")
        if not step.get("title") or not step.get("description"):
            raise AssertionError("Every Node 3 step must include title and description.")
        if not _contains_hangul(step["title"]) or not _contains_hangul(step["description"]):
            raise AssertionError("Node 3 title and description should be written in Korean.")
        if not isinstance(step.get("estimated_hours"), int):
            raise AssertionError("Every Node 3 step must include integer estimated_hours.")
        if not set(step.get("course_source_row_numbers") or []).issubset(valid_courses):
            raise AssertionError("Node 3 used a course id that was not present in Node 2 results.")
        if not set(step.get("resource_external_ids") or []).issubset(valid_resources):
            raise AssertionError("Node 3 used a resource id that was not present in Node 2 results.")
        if has_search_references and not (
            step.get("course_source_row_numbers") or step.get("resource_external_ids")
        ):
            raise AssertionError("Every Node 3 step should reference at least one Node 2 search result.")


def _topic_slugs(topics: list[dict[str, Any]]) -> list[str]:
    return [str(topic.get("slug")) for topic in topics if topic.get("slug")]


def _first_value(items: list[dict[str, Any]], key: str) -> Any:
    if not items:
        return None
    return items[0].get(key)


def _contains_hangul(value: str) -> bool:
    return any("가" <= char <= "힣" for char in value)


def _print_summary(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _print_full_json(value: dict[str, Any], enabled: bool) -> None:
    if enabled:
        print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
