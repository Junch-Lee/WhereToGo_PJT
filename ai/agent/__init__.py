"""Agent package for the WhereToGo curriculum workflow."""

from __future__ import annotations

from importlib import import_module

AgentState = import_module(".00_state", __name__).AgentState

__all__ = ["AgentState"]
