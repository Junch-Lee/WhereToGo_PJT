"""04_node : Node 1 entry point for user input analysis."""

from __future__ import annotations

from importlib import import_module
import logging

_form_normalizer = import_module("ai.agent.nodes.input_analysis.01_form_normalizer")
_topic_catalog = import_module("ai.agent.nodes.input_analysis.02_topic_catalog")
_llm_analyzer = import_module("ai.agent.nodes.input_analysis.03_llm_analyzer")

normalize_form = _form_normalizer.normalize_form
match_candidates = _topic_catalog.match_candidates
expand_context = _topic_catalog.expand_context
extract_unmatched_terms = _topic_catalog.extract_unmatched_terms
analyze_with_llm = _llm_analyzer.analyze_with_llm

logger = logging.getLogger(__name__)


def run_input_analysis(raw_input: dict, catalog: list[dict]) -> dict:
    """Analyze user input and return fields to merge into AgentState."""
    if not isinstance(catalog, list):
        raise TypeError("catalog must be a list of dicts.")

    user_profile = normalize_form(raw_input)
    goal_text = user_profile["goal"]
    candidates = match_candidates(goal_text, catalog)
    context_candidates = expand_context(candidates, catalog)

    llm_result = analyze_with_llm(
        goal_text=goal_text,
        purpose=user_profile["purpose"],
        candidates=candidates,
        context_candidates=context_candidates,
    )
    unmatched_terms = extract_unmatched_terms(goal_text, candidates)
    if not llm_result.get("unmatched_terms"):
        llm_result["unmatched_terms"] = unmatched_terms

    topic_analysis = {
        "original_input": llm_result.get("original_input", goal_text),
        "target_topics": list(llm_result.get("target_topics") or []),
        "context_topics": list(llm_result.get("context_topics") or []),
        "prerequisite_candidates": list(llm_result.get("prerequisite_candidates") or []),
        "unmatched_terms": list(llm_result.get("unmatched_terms") or []),
        "needs_clarification": bool(llm_result.get("needs_clarification", False)),
        "clarification_question": str(llm_result.get("clarification_question") or ""),
    }

    search_query = str(llm_result.get("search_query") or goal_text).strip()
    is_in_scope = bool(llm_result.get("is_in_scope", False))

    logger.info(
        "Input analysis completed: in_scope=%s targets=%s",
        is_in_scope,
        [topic.get("slug") for topic in topic_analysis["target_topics"]],
    )

    return {
        "user_profile": user_profile,
        "topic_analysis": topic_analysis,
        "search_query": search_query,
        "is_in_scope": is_in_scope,
    }
