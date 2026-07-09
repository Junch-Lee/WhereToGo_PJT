"""ChromaDB 기반 RAG 검색 모듈.

예시:
    search("머신러닝 입문", resource_filter={"difficulty_level": "beginner"})
    search("자료구조", course_filter={"grade": {"$lte": 2}})
    search("인공지능", course_filter={"department_name": "컴퓨터공학과"})
"""

from __future__ import annotations

from typing import Any

from ai.core.chroma_client import get_courses_collection, get_resources_collection
from ai.core.embeddings import create_openai_embedding_function

# 검색 시마다 임베딩 함수를 새로 만들지 않도록 모듈 로드 시 1회만 생성합니다.
_EMBEDDING_FUNCTION = create_openai_embedding_function()
_COURSES_COLLECTION = get_courses_collection(embedding_function=_EMBEDDING_FUNCTION)
_RESOURCES_COLLECTION = get_resources_collection(embedding_function=_EMBEDDING_FUNCTION)


def search(
    query: str,
    n_courses: int = 5,
    n_resources: int = 5,
    course_filter: dict | None = None,
    resource_filter: dict | None = None,
) -> dict:
    """쿼리로 courses와 resources를 동시 검색하여 용도별로 분리 반환합니다.

    Args:
        query: 사용자 검색 문장입니다.
        n_courses: 반환할 강의계획서 검색 결과 수입니다.
        n_resources: 반환할 학습 자료 검색 결과 수입니다.
        course_filter: courses 컬렉션에 적용할 ChromaDB where 딕셔너리입니다.
        resource_filter: resources 컬렉션에 적용할 ChromaDB where 딕셔너리입니다.

    Returns:
        {"courses": [...], "resources": [...]} 형태의 검색 결과입니다.
    """
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("검색 쿼리는 비어 있을 수 없습니다.")

    return {
        "courses": _search_collection(
            _COURSES_COLLECTION,
            normalized_query,
            n_courses,
            where=course_filter,
        ),
        "resources": _search_collection(
            _RESOURCES_COLLECTION,
            normalized_query,
            n_resources,
            where=resource_filter,
        ),
    }


def _search_collection(
    collection: Any,
    query: str,
    n_results: int,
    where: dict | None = None,
) -> list[dict]:
    """단일 컬렉션 검색 후 결과를 표준 형식 list[dict]로 변환합니다."""
    if n_results <= 0:
        return []

    collection_count = int(collection.count())
    if collection_count == 0:
        return []

    query_args: dict[str, Any] = {
        "query_texts": [query],
        "n_results": min(n_results, collection_count),
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        query_args["where"] = where

    raw_result = collection.query(**query_args)
    return _format_query_result(raw_result)


def _format_query_result(raw_result: dict) -> list[dict]:
    """ChromaDB query 결과를 RAG 검색 표준 결과로 변환합니다."""
    ids = _first_result_group(raw_result.get("ids"))
    documents = _first_result_group(raw_result.get("documents"))
    metadatas = _first_result_group(raw_result.get("metadatas"))
    distances = _first_result_group(raw_result.get("distances"))

    results: list[dict] = []
    for index, doc_id in enumerate(ids):
        distance = _safe_get(distances, index)
        results.append(
            {
                "id": doc_id,
                "score": _distance_to_score(distance),
                "document": _safe_get(documents, index, default=""),
                "metadata": _safe_get(metadatas, index, default={}),
            }
        )
    return results


def _distance_to_score(distance: Any) -> float:
    """ChromaDB cosine distance를 높을수록 좋은 score로 변환합니다."""
    if distance is None:
        return 0.0
    return 1.0 - float(distance)


def _first_result_group(value: Any) -> list:
    """ChromaDB의 첫 번째 query 결과 그룹을 안전하게 꺼냅니다."""
    if not value:
        return []
    return list(value[0])


def _safe_get(values: list, index: int, default: Any = None) -> Any:
    """리스트 범위를 벗어나면 기본값을 반환합니다."""
    if index >= len(values):
        return default
    return values[index]
