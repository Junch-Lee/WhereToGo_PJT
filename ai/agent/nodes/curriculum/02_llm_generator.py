"""02_llm_generator: GMS/OpenAI 호환 LLM 호출 및 JSON 파싱."""

from __future__ import annotations

import json
import logging
import os
import re

from openai import OpenAI

logger = logging.getLogger(__name__)

DEFAULT_CHAT_MODEL = "gpt-4o-mini"


def generate_curriculum(messages: list[dict]) -> dict:
    """LLM 응답을 커리큘럼 JSON dict로 반환한다."""
    if not messages:
        raise ValueError("messages must not be empty.")

    try:
        from ai.core.config import settings

        if not settings.gms_key:
            raise RuntimeError("GMS_KEY is required for curriculum generation.")

        client = OpenAI(api_key=settings.gms_key, base_url=settings.openai_base_url)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_CHAT_MODEL", DEFAULT_CHAT_MODEL),
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or ""
        return _parse_json_object(content)
    except Exception:
        logger.exception("Curriculum LLM generation failed.")
        raise


def _parse_json_object(content: str) -> dict:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group(0))

    if not isinstance(parsed, dict):
        raise ValueError("Curriculum LLM response must be a JSON object.")
    return parsed

