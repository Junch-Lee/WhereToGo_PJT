"""실제 ChromaDB 검색 품질을 육안 확인하는 스크립트."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.search.searcher import search  # noqa: E402


TEST_CASES = [
    {
        "title": "일반 검색",
        "query": "파이썬 프로그래밍 배우고 싶어요",
    },
    {
        "title": "난이도 검색",
        "query": "머신러닝 입문 강의",
    },
    {
        "title": "난이도 검색 + beginner 필터",
        "query": "머신러닝 입문 강의",
        "resource_filter": {"difficulty_level": "beginner"},
    },
    {
        "title": "선수지식 맥락",
        "query": "딥러닝 배우려면 무엇부터?",
    },
    {
        "title": "학년 필터",
        "query": "자료구조",
        "course_filter": {"grade": {"$lte": 2}},
    },
    {
        "title": "주제 검색",
        "query": "데이터베이스",
    },
    {
        "title": "짧은 쿼리",
        "query": "AI",
    },
]


def main() -> None:
    """테스트 쿼리셋으로 courses/resources 상위 결과를 출력합니다."""
    for case in TEST_CASES:
        print("=" * 80)
        print(f"[{case['title']}] {case['query']}")

        result = search(
            case["query"],
            n_courses=3,
            n_resources=3,
            course_filter=case.get("course_filter"),
            resource_filter=case.get("resource_filter"),
        )

        _print_courses(result["courses"])
        _print_resources(result["resources"])


def _print_courses(courses: list[dict]) -> None:
    """강의 검색 결과를 한 줄 요약으로 출력합니다."""
    print("\n courses")
    if not courses:
        print("  - 결과 없음")
        return

    for item in courses:
        metadata = item["metadata"]
        print(
            "  - "
            f"{metadata.get('course_name', '(과목명 없음)')} | "
            f"{metadata.get('department_name', '(학과 없음)')} | "
            f"score={item['score']:.4f}"
        )


def _print_resources(resources: list[dict]) -> None:
    """학습 자료 검색 결과를 한 줄 요약으로 출력합니다."""
    print("\n resources")
    if not resources:
        print("  - 결과 없음")
        return

    for item in resources:
        metadata = item["metadata"]
        print(
            "  - "
            f"{metadata.get('title', '(자료명 없음)')} | "
            f"{metadata.get('difficulty_level', 'unknown')} | "
            f"score={item['score']:.4f}"
        )


if __name__ == "__main__":
    main()
