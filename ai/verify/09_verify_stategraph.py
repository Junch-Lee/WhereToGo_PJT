"""Verify the StateGraph agent integration.

Default mode uses fake nodes to verify graph routing without network calls:
    python ai/verify/09_verify_stategraph.py

GMS mode runs the full API-backed pipeline:
    python ai/verify/09_verify_stategraph.py --gms --json

Prerequisites for --gms:
    set GMS_KEY=sk-...
    set OPENAI_BASE_URL=https://api.openai.com/v1
    set OPENAI_CHAT_MODEL=gpt-4o-mini
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

import ai.agent.graph as agent_graph  # noqa: E402
from ai.agent import run_agent  # noqa: E402


GMS_RAW_INPUT = {
    "goal_text": "머신러닝을 배우고 싶고 필요한 수학 기초도 함께 보완하고 싶어",
    "purpose": "취업/이직",
    "level": "완전 입문",
    "period": "3~4개월",
    "weekly_hours": "10~15시간",
    "learning_style": "프로젝트 중심",
    "concern": "",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the StateGraph agent integration.")
    parser.add_argument("--gms", action="store_true", help="Run the real GMS/API-backed pipeline.")
    parser.add_argument("--json", action="store_true", help="Print the full final AgentState.")
    args = parser.parse_args()

    if args.gms:
        _run_gms_pipeline(print_json=args.json)
        return

    _run_fake_graph_checks()


def _run_fake_graph_checks() -> None:
    calls = {"search": 0, "curriculum": 0}
    originals = {
        "run_input_analysis": agent_graph.run_input_analysis,
        "run_search": agent_graph.run_search,
        "run_curriculum_generation": agent_graph.run_curriculum_generation,
    }

    agent_graph.run_input_analysis = _fake_input_analysis
    agent_graph.run_search = _make_fake_search(calls)
    agent_graph.run_curriculum_generation = _make_fake_curriculum(calls)

    try:
        _assert_normal_case(calls)
        _assert_out_of_scope_case(calls)
        _assert_empty_search_case(calls)
    finally:
        agent_graph.run_input_analysis = originals["run_input_analysis"]
        agent_graph.run_search = originals["run_search"]
        agent_graph.run_curriculum_generation = originals["run_curriculum_generation"]

    print("OK: StateGraph fake routing checks passed.")


def _assert_normal_case(calls: dict[str, int]) -> None:
    before = dict(calls)
    result = agent_graph.run_agent({"case": "normal"}, catalog=[{"slug": "python"}])

    if result.get("generation_status") != "generated":
        raise AssertionError("normal case must generate a curriculum.")
    if not result.get("curriculum"):
        raise AssertionError("normal case must include curriculum.")
    if calls["search"] != before["search"] + 1:
        raise AssertionError("normal case must call Node 2 exactly once.")
    if calls["curriculum"] != before["curriculum"] + 1:
        raise AssertionError("normal case must call Node 3 exactly once.")


def _assert_out_of_scope_case(calls: dict[str, int]) -> None:
    before = dict(calls)
    result = agent_graph.run_agent({"case": "out_of_scope"}, catalog=[{"slug": "python"}])

    if result.get("generation_status") != "out_of_scope":
        raise AssertionError("out-of-scope case must terminate with out_of_scope.")
    if result.get("curriculum") is not None:
        raise AssertionError("out-of-scope case must not include curriculum.")
    if calls != before:
        raise AssertionError("out-of-scope case must not call Node 2 or Node 3.")


def _assert_empty_search_case(calls: dict[str, int]) -> None:
    before = dict(calls)
    result = agent_graph.run_agent({"case": "empty_search"}, catalog=[{"slug": "python"}])

    if result.get("generation_status") != "insufficient_search_results":
        raise AssertionError("empty-search case must terminate with insufficient_search_results.")
    if result.get("curriculum") is not None:
        raise AssertionError("empty-search case must not include curriculum.")
    if calls["search"] != before["search"] + 1:
        raise AssertionError("empty-search case must call Node 2 exactly once.")
    if calls["curriculum"] != before["curriculum"]:
        raise AssertionError("empty-search case must not call Node 3.")


def _fake_input_analysis(raw_input: dict, catalog: list[dict]) -> dict[str, Any]:
    if not isinstance(catalog, list):
        raise TypeError("catalog must be a list of dicts.")

    case = raw_input.get("case")
    is_in_scope = case != "out_of_scope"
    search_query = "empty search" if case == "empty_search" else "python programming"

    return {
        "user_profile": {"goal": search_query, "difficulty_level": "beginner"},
        "topic_analysis": {
            "target_topics": [{"slug": "python", "name": "Python"}],
            "context_topics": [],
            "prerequisite_candidates": [],
            "unmatched_terms": [],
            "needs_clarification": not is_in_scope,
            "clarification_question": "",
        },
        "search_query": search_query,
        "is_in_scope": is_in_scope,
    }


def _make_fake_search(calls: dict[str, int]):
    def fake_search(state: dict[str, Any]) -> dict[str, Any]:
        calls["search"] += 1
        if state.get("search_query") == "empty search":
            courses: list[dict[str, Any]] = []
            resources: list[dict[str, Any]] = []
        else:
            courses = [{"source_row_number": 1, "course_name": "Python Basics", "score": 0.95}]
            resources = [{"external_id": "res-1", "title": "Python Guide", "score": 0.91}]

        return {
            "search_results": {
                "query": state.get("search_query", ""),
                "filters": {"course_filter": None, "resource_filter": None},
                "courses": courses,
                "resources": resources,
            }
        }

    return fake_search


def _make_fake_curriculum(calls: dict[str, int]):
    def fake_curriculum(state: dict[str, Any]) -> dict[str, Any]:
        calls["curriculum"] += 1
        return {
            "curriculum": {
                "title": "Python Curriculum",
                "difficulty_level": "beginner",
                "recommendation_reason": "Verified by fake graph routing.",
                "steps": [
                    {
                        "step_order": 1,
                        "title": "Python Basics",
                        "description": "Learn syntax and basic programming.",
                        "estimated_hours": 8,
                        "difficulty_level": "beginner",
                        "target_topic_slug": "python",
                        "prerequisite_note": "",
                        "course_source_row_numbers": [1],
                        "resource_external_ids": ["res-1"],
                    }
                ],
            },
            "generation_status": "generated",
            "message": "",
        }

    return fake_curriculum


def _run_gms_pipeline(print_json: bool) -> None:
    from ai.agent.nodes.input_analysis import SAMPLE_TOPIC_CATALOG
    from ai.core.config import settings

    if not settings.gms_key:
        raise RuntimeError("GMS_KEY is required for --gms mode.")

    result = run_agent(GMS_RAW_INPUT, SAMPLE_TOPIC_CATALOG)
    _assert_gms_result(result)

    curriculum = result["curriculum"]
    search_results = result["search_results"]
    summary = {
        "generation_status": result["generation_status"],
        "search_query": result["search_query"],
        "course_count": len(search_results.get("courses") or []),
        "resource_count": len(search_results.get("resources") or []),
        "title": curriculum["title"],
        "step_count": len(curriculum["steps"]),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if print_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    print("OK: StateGraph GMS pipeline completed.")


def _assert_gms_result(result: dict[str, Any]) -> None:
    if result.get("generation_status") != "generated":
        raise AssertionError("GMS pipeline must finish with generation_status='generated'.")
    if not result.get("is_in_scope"):
        raise AssertionError("GMS sample should be classified as in scope.")
    if not result.get("search_query"):
        raise AssertionError("GMS pipeline must include search_query.")

    search_results = result.get("search_results") or {}
    if not (search_results.get("courses") or search_results.get("resources")):
        raise AssertionError(
            "GMS pipeline returned no RAG results. Run: python -m ai.indexing.indexer --target all --reset"
        )

    curriculum = result.get("curriculum") or {}
    if not curriculum.get("title"):
        raise AssertionError("GMS pipeline curriculum must include title.")
    if not curriculum.get("steps"):
        raise AssertionError("GMS pipeline curriculum must include at least one step.")


if __name__ == "__main__":
    main()
