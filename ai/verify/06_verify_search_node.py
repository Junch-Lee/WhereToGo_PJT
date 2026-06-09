"""Verify Node 2 search adapter without calling the real embedding API."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.agent.nodes.search import run_search


NORMAL_STATE = {
    "user_profile": {
        "goal": "머신러닝 배우고 싶고 수학도 보완하고 싶어요",
        "difficulty_level": "beginner",
    },
    "topic_analysis": {
        "target_topics": [
            {"slug": "machine-learning", "name": "머신러닝", "depth": 3},
        ],
        "prerequisite_candidates": [
            {"slug": "mathematics-for-cs", "name": "컴퓨터공학 수학"},
        ],
    },
    "search_query": "머신러닝 입문",
    "is_in_scope": True,
}

OUT_OF_SCOPE_STATE = {
    "user_profile": {"difficulty_level": "beginner"},
    "topic_analysis": {},
    "search_query": "영어 회화",
    "is_in_scope": False,
}


def main() -> None:
    print("## normal_search")
    print(json.dumps(run_search(NORMAL_STATE, search_fn=_fake_search), ensure_ascii=False, indent=2))

    print("\n## out_of_scope")
    print(json.dumps(run_search(OUT_OF_SCOPE_STATE, search_fn=_fake_search), ensure_ascii=False, indent=2))


def _fake_search(
    query: str,
    n_courses: int,
    n_resources: int,
    course_filter: dict | None,
    resource_filter: dict | None,
) -> dict:
    print(
        json.dumps(
            {
                "called_query": query,
                "n_courses": n_courses,
                "n_resources": n_resources,
                "course_filter": course_filter,
                "resource_filter": resource_filter,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return {
        "courses": [
            {
                "id": "course_10164",
                "score": 0.91,
                "metadata": {
                    "source_row_number": 10164,
                    "course_name": "머신러닝",
                    "topic_names": "머신러닝, 인공지능",
                },
            }
        ],
        "resources": [
            {
                "id": "resource_KOCW_abc123",
                "score": 0.88,
                "metadata": {
                    "external_id": "abc123",
                    "title": "머신러닝 입문",
                    "difficulty_level": "beginner",
                    "topic_names": "머신러닝, 선형대수",
                },
            }
        ],
    }


if __name__ == "__main__":
    main()

