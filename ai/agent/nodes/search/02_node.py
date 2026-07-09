"""02_node: 기존 RAG searcher를 호출하고 Node 3용 결과로 가공."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
import logging
from typing import Any

from ai.agent.nodes.search import build_resource_filter, build_search_query

logger = logging.getLogger(__name__)

DEFAULT_N_COURSES = 5
DEFAULT_N_RESOURCES = 8


def run_search(state: dict, search_fn: Callable[..., dict] | None = None) -> dict:
    """Node 1 분석 결과를 바탕으로 RAG 검색을 수행한다."""
    if not state.get("is_in_scope", False):
        logger.info("Node 2 search skipped: is_in_scope=false")
        return {"search_results": _empty_search_results(skipped=True)}

    user_profile = state.get("user_profile") or {}
    topic_analysis = state.get("topic_analysis") or {}
    query = build_search_query(str(state.get("search_query") or ""), topic_analysis)
    resource_filter = build_resource_filter(user_profile)

    search_fn = search_fn or _load_searcher()
    try:
        raw_results = search_fn(
            query,
            n_courses=DEFAULT_N_COURSES,
            n_resources=DEFAULT_N_RESOURCES,
            course_filter=None,
            resource_filter=resource_filter,
        )
    except Exception:
        logger.exception("Node 2 RAG search failed.")
        raise

    courses = [_format_course(item) for item in raw_results.get("courses", [])]
    resources = [_format_resource(item) for item in raw_results.get("resources", [])]
    courses = [item for item in courses if item is not None]
    resources = [item for item in resources if item is not None]

    logger.info(
        "Node 2 search completed: courses=%s resources=%s query=%s",
        len(courses),
        len(resources),
        query,
    )

    return {
        "search_results": {
            "query": query,
            "filters": {
                "course_filter": None,
                "resource_filter": resource_filter,
            },
            "courses": courses,
            "resources": resources,
        }
    }


def _load_searcher() -> Callable[..., dict]:
    return import_module("ai.search.searcher").search


def _empty_search_results(skipped: bool = False) -> dict:
    return {
        "query": "",
        "filters": {
            "course_filter": None,
            "resource_filter": None,
        },
        "courses": [],
        "resources": [],
        "skipped": skipped,
    }


def _format_course(item: dict) -> dict | None:
    metadata = dict(item.get("metadata") or {})
    source_row_number = metadata.get("source_row_number")
    if source_row_number in (None, ""):
        logger.warning("Course search result skipped: missing source_row_number id=%s", item.get("id"))
        return None

    return {
        "source_row_number": _to_int(source_row_number),
        "course_name": _clean_text(metadata.get("course_name")),
        "score": _to_float(item.get("score")),
        "metadata": metadata,
    }


def _format_resource(item: dict) -> dict | None:
    metadata = dict(item.get("metadata") or {})
    external_id = _clean_text(metadata.get("external_id"))
    if not external_id:
        logger.warning("Resource search result skipped: missing external_id id=%s", item.get("id"))
        return None

    return {
        "external_id": external_id,
        "title": _clean_text(metadata.get("title")),
        "score": _to_float(item.get("score")),
        "metadata": metadata,
    }


def _clean_text(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

