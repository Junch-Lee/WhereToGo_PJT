"""Verify Node 1 input analysis with a sample topic catalog."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

os.environ["GMS_KEY"] = ""

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.agent.nodes.input_analysis import SAMPLE_TOPIC_CATALOG, run_input_analysis


CASES = [
    {
        "name": "normal_machine_learning",
        "raw_input": {
            "goal_text": "머신러닝 배우고 싶고 수학도 보완하고 싶어요",
            "purpose": "취업/이직",
            "level": "완전 입문",
            "period": "3~4개월",
            "weekly_hours": "10~15h",
            "learning_style": "프로젝트 중심",
            "concern": "",
        },
    },
    {
        "name": "out_of_scope_english",
        "raw_input": {
            "goal_text": "영어 회화 배우고 싶어요",
            "purpose": "자기계발",
            "level": "완전 입문",
            "period": "1~2개월",
            "weekly_hours": "7h",
            "learning_style": "균형",
            "concern": "",
        },
    },
    {
        "name": "ambiguous_development",
        "raw_input": {
            "goal_text": "개발 잘하고 싶어요",
            "purpose": "취업/이직",
            "level": "기초 있음",
            "period": "정하지 않음",
            "weekly_hours": "",
            "learning_style": "",
            "concern": "",
        },
    },
]


def main() -> None:
    for case in CASES:
        result = run_input_analysis(case["raw_input"], SAMPLE_TOPIC_CATALOG)
        print(f"\n## {case['name']}")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
