"""Build topic-name lookup maps from reviewed topic mapping CSV files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

COURSE_LOOKUP_COLUMN = "curriculum_course_lookup_key"
RESOURCE_LOOKUP_COLUMN = "learning_resource_lookup_key"
TOPIC_NAME_COLUMN = "topic_name"


def build_course_topic_map(csv_path: str | Path) -> dict:
    """Return course lookup key to comma-separated topic names.

    Args:
        csv_path: Path to final_course_topics_import.csv.

    Returns:
        Dict keyed by curriculum_courses.source_row_number.
    """
    return _build_topic_map(csv_path, COURSE_LOOKUP_COLUMN, cast_key_to_int=True)


def build_resource_topic_map(csv_path: str | Path) -> dict:
    """Return resource lookup key to comma-separated topic names.

    Args:
        csv_path: Path to final_resource_topics_import.csv.

    Returns:
        Dict keyed by learning_resource.external_id.
    """
    return _build_topic_map(csv_path, RESOURCE_LOOKUP_COLUMN, cast_key_to_int=False)


def _build_topic_map(
    csv_path: str | Path,
    lookup_column: str,
    cast_key_to_int: bool,
) -> dict:
    """Load a mapping CSV and group topic names by source lookup key."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Topic mapping CSV not found: {path}")

    df = pd.read_csv(path)
    if df.empty:
        return {}

    missing_columns = {lookup_column, TOPIC_NAME_COLUMN} - set(df.columns)
    if missing_columns:
        raise ValueError(f"Topic mapping CSV is missing columns: {missing_columns}")

    topic_map: dict = {}
    for _, row in df.iterrows():
        raw_key = row.get(lookup_column)
        topic_name = _clean_text(row.get(TOPIC_NAME_COLUMN))
        if pd.isna(raw_key) or not topic_name:
            continue

        key = int(raw_key) if cast_key_to_int else str(raw_key).strip()
        topic_map.setdefault(key, [])
        if topic_name not in topic_map[key]:
            topic_map[key].append(topic_name)

    return {key: ", ".join(topic_names) for key, topic_names in topic_map.items()}


def _clean_text(value: object) -> str:
    """Normalize missing values to an empty string and trim text."""
    if _is_missing_value(value):
        return ""
    return str(value).strip()


def _is_missing_value(value: Any) -> bool:
    """Return True for scalar values that pandas treats as missing."""
    if value is None:
        return True
    return bool(pd.isna(value))
