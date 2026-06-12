"""Node 3 curriculum generation package."""

from __future__ import annotations

from importlib import import_module

build_curriculum_prompt = import_module(".01_prompt_builder", __name__).build_curriculum_prompt
generate_curriculum = import_module(".02_llm_generator", __name__).generate_curriculum
validate_curriculum = import_module(".03_validator", __name__).validate_curriculum
run_curriculum_generation = import_module(".04_node", __name__).run_curriculum_generation

__all__ = [
    "build_curriculum_prompt",
    "generate_curriculum",
    "run_curriculum_generation",
    "validate_curriculum",
]

