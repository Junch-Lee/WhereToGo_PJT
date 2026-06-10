"""Verify Node 3 curriculum generation with a fake LLM response."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.agent.nodes.curriculum import run_curriculum_generation


NORMAL_STATE = {
    "is_in_scope": True,
    "user_profile": {
        "goal": "머신러닝 배우고 싶고 수학도 보완하고 싶어요",
        "purpose": "취업/이직",
        "difficulty_level": "beginner",
        "target_weeks": 16,
        "weekly_available_hours": 12,
        "preferred_learning_style": "project",
    },
    "topic_analysis": {
        "target_topics": [{"slug": "machine-learning", "name": "머신러닝"}],
        "context_topics": [{"slug": "artificial-intelligence", "name": "인공지능"}],
        "prerequisite_candidates": [{"slug": "mathematics-for-cs", "name": "컴퓨터공학 수학"}],
    },
    "search_results": {
        "courses": [
            {
                "source_row_number": 10164,
                "course_name": "머신러닝",
                "score": 0.91,
                "metadata": {"topic_names": "머신러닝, 인공지능"},
            }
        ],
        "resources": [
            {
                "external_id": "abc123",
                "title": "머신러닝 입문",
                "score": 0.88,
                "metadata": {"topic_names": "머신러닝, 선형대수", "difficulty_level": "beginner"},
            }
        ],
    },
}

OUT_OF_SCOPE_STATE = {
    "is_in_scope": False,
    "user_profile": {},
    "topic_analysis": {},
    "search_results": {"courses": [], "resources": []},
}

EMPTY_SEARCH_STATE = {
    "is_in_scope": True,
    "user_profile": NORMAL_STATE["user_profile"],
    "topic_analysis": NORMAL_STATE["topic_analysis"],
    "search_results": {"courses": [], "resources": []},
}


def main() -> None:
    print("## normal_generation")
    print(json.dumps(run_curriculum_generation(NORMAL_STATE, _fake_generator), ensure_ascii=False, indent=2))

    print("\n## out_of_scope")
    print(json.dumps(run_curriculum_generation(OUT_OF_SCOPE_STATE, _fake_generator), ensure_ascii=False, indent=2))

    print("\n## empty_search")
    print(json.dumps(run_curriculum_generation(EMPTY_SEARCH_STATE, _fake_generator), ensure_ascii=False, indent=2))


def _fake_generator(messages: list[dict]) -> dict:
    print("prompt_messages:", len(messages))
    return {
        "title": "머신러닝 입문 16주 커리큘럼",
        "difficulty_level": "beginner",
        "recommendation_reason": "목표와 검색 결과를 바탕으로 수학 기초부터 머신러닝 실습까지 구성했습니다.",
        "steps": [
            {
                "step_order": 10,
                "title": "수학 기초 보완",
                "description": "머신러닝 학습에 필요한 수학 기초를 정리합니다.",
                "target_topic_slug": "unknown-topic",
                "difficulty_level": "beginner",
                "estimated_hours": 24,
                "prerequisite_note": "수학 기초가 부족하면 먼저 진행합니다.",
                "course_source_row_numbers": [10164, 99999],
                "resource_external_ids": ["abc123", "ghost-resource"],
            },
            {
                "step_order": 20,
                "title": "머신러닝 핵심 개념",
                "description": "지도학습과 모델 평가를 학습합니다.",
                "target_topic_slug": "machine-learning",
                "difficulty_level": "beginner",
                "estimated_hours": 36,
                "prerequisite_note": "",
                "course_source_row_numbers": [10164],
                "resource_external_ids": ["abc123"],
            },
        ],
    }


if __name__ == "__main__":
    main()

