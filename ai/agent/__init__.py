"""Agent package for the WhereToGo curriculum workflow."""

from __future__ import annotations

from importlib import import_module

AgentState = import_module(".00_state", __name__).AgentState


def run_agent(raw_input: dict, catalog: list[dict]) -> dict:
    """Run the StateGraph-backed agent workflow."""
    return import_module(".graph", __name__).run_agent(raw_input, catalog)


__all__ = ["AgentState", "run_agent"]
