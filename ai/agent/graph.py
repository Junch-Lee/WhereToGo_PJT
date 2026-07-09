"""StateGraph integration for the WhereToGo agent workflow."""

from __future__ import annotations

import logging
from collections.abc import Callable
from importlib import import_module
from typing import Any

from ai.agent import AgentState

try:
    from langgraph.graph import END, START, StateGraph
except ModuleNotFoundError:
    END = "__end__"
    START = "__start__"
    StateGraph = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

NodeFn = Callable[[AgentState], dict[str, Any]]


def make_input_analysis_node(catalog: list[dict]) -> NodeFn:
    """Bind the external topic catalog to the Node 1 LangGraph signature."""

    def node(state: AgentState) -> dict[str, Any]:
        return run_input_analysis(state["raw_input"], catalog)

    return node


def run_input_analysis(raw_input: dict, catalog: list[dict]) -> dict[str, Any]:
    """Lazy wrapper for Node 1 to keep graph imports lightweight."""
    return import_module("ai.agent.nodes.input_analysis").run_input_analysis(raw_input, catalog)


def run_search(state: dict[str, Any]) -> dict[str, Any]:
    """Lazy wrapper for Node 2."""
    return import_module("ai.agent.nodes.search").run_search(state)


def run_curriculum_generation(state: dict[str, Any]) -> dict[str, Any]:
    """Lazy wrapper for Node 3."""
    return import_module("ai.agent.nodes.curriculum").run_curriculum_generation(state)


def route_after_input_analysis(state: AgentState) -> str:
    """Route to search only when Node 1 classified the request as in scope."""
    if state.get("is_in_scope"):
        logger.info("Agent graph route: input_analysis -> search")
        return "search"

    logger.info("Agent graph route: input_analysis -> out_of_scope")
    return "out_of_scope"


def route_after_search(state: AgentState) -> str:
    """Route to generation only when RAG returned usable evidence."""
    search_results = state.get("search_results") or {}
    if search_results.get("courses") or search_results.get("resources"):
        logger.info("Agent graph route: search -> curriculum")
        return "curriculum"

    logger.info("Agent graph route: search -> insufficient_search_results")
    return "insufficient_search_results"


def out_of_scope_node(state: AgentState) -> dict[str, Any]:
    """Return a normal terminal state for non-CS or unsupported goals."""
    return {
        "curriculum": None,
        "generation_status": "out_of_scope",
        "message": "현재는 컴퓨터공학 분야 커리큘럼만 생성할 수 있습니다.",
    }


def insufficient_search_results_node(state: AgentState) -> dict[str, Any]:
    """Return a normal terminal state when RAG evidence is unavailable."""
    return {
        "curriculum": None,
        "generation_status": "insufficient_search_results",
        "message": "커리큘럼 생성에 필요한 검색 결과가 부족합니다.",
    }


def build_agent_graph(catalog: list[dict]):
    """Build the executable StateGraph for Node 1 -> Node 2 -> Node 3."""
    if StateGraph is None:
        logger.warning("langgraph is not installed; using compatibility graph runner.")
        return _CompatCompiledGraph(catalog)

    graph = StateGraph(AgentState)

    graph.add_node("input_analysis", make_input_analysis_node(catalog))
    graph.add_node("search", run_search)
    graph.add_node("curriculum", run_curriculum_generation)
    graph.add_node("out_of_scope", out_of_scope_node)
    graph.add_node("insufficient_search_results", insufficient_search_results_node)

    graph.add_edge(START, "input_analysis")
    graph.add_conditional_edges(
        "input_analysis",
        route_after_input_analysis,
        {
            "search": "search",
            "out_of_scope": "out_of_scope",
        },
    )
    graph.add_conditional_edges(
        "search",
        route_after_search,
        {
            "curriculum": "curriculum",
            "insufficient_search_results": "insufficient_search_results",
        },
    )
    graph.add_edge("curriculum", END)
    graph.add_edge("out_of_scope", END)
    graph.add_edge("insufficient_search_results", END)

    return graph.compile()


def run_agent(raw_input: dict, catalog: list[dict]) -> dict[str, Any]:
    """Run the full agent pipeline and return the final merged AgentState."""
    logger.info("Agent graph started.")
    graph = build_agent_graph(catalog)
    result = graph.invoke({"raw_input": raw_input})
    logger.info("Agent graph completed: status=%s", result.get("generation_status"))
    return dict(result)


class _CompatCompiledGraph:
    """Minimal runner used only when langgraph is missing in the local env."""

    def __init__(self, catalog: list[dict]) -> None:
        self.input_analysis_node = make_input_analysis_node(catalog)

    def invoke(self, initial_state: AgentState) -> dict[str, Any]:
        state: AgentState = dict(initial_state)
        state.update(self.input_analysis_node(state))

        if route_after_input_analysis(state) == "out_of_scope":
            state.update(out_of_scope_node(state))
            return state

        state.update(run_search(state))
        if route_after_search(state) == "insufficient_search_results":
            state.update(insufficient_search_results_node(state))
            return state

        state.update(run_curriculum_generation(state))
        return state
