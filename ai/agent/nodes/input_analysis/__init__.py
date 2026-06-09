"""Input analysis node."""

from __future__ import annotations

from importlib import import_module

SAMPLE_TOPIC_CATALOG = import_module(
    ".00_sample_catalog",
    __name__,
).SAMPLE_TOPIC_CATALOG
run_input_analysis = import_module(".04_node", __name__).run_input_analysis

__all__ = ["SAMPLE_TOPIC_CATALOG", "run_input_analysis"]
