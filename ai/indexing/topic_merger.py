"""토픽 매핑 CSV를 문서 생성용 dict로 변환하는 모듈."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

COURSE_LOOKUP_COLUMN = "curriculum_course_lookup_key"
RESOURCE_LOOKUP_COLUMN = "learning_resource_lookup_key"
TOPIC_NAME_COLUMN = "topic_name"


def build_course_topic_map(csv_path: str | Path) -> dict:
    """강의별 연결 토픽명을 쉼표 구분 문자열로 집계합니다.

    Args:
        csv_path: final_course_topics_import.csv 경로입니다.

    Returns:
        source_row_number(int)를 키로, 토픽명 문자열을 값으로 갖는 dict입니다.
    """
    return _build_topic_map(csv_path, COURSE_LOOKUP_COLUMN, cast_key_to_int=True)


def build_resource_topic_map(csv_path: str | Path) -> dict:
    """학습 자료별 연결 토픽명을 쉼표 구분 문자열로 집계합니다.

    Args:
        csv_path: final_resource_topics_import.csv 경로입니다.

    Returns:
        external_id(str)를 키로, 토픽명 문자열을 값으로 갖는 dict입니다.
    """
    return _build_topic_map(csv_path, RESOURCE_LOOKUP_COLUMN, cast_key_to_int=False)


def _build_topic_map(
    csv_path: str | Path,
    lookup_column: str,
    cast_key_to_int: bool,
) -> dict:
    """토픽 매핑 CSV를 공통 규칙으로 집계합니다."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"토픽 매핑 CSV를 찾을 수 없습니다: {path}")

    df = pd.read_csv(path)
    if df.empty:
        return {}

    missing_columns = {lookup_column, TOPIC_NAME_COLUMN} - set(df.columns)
    if missing_columns:
        raise ValueError(f"토픽 매핑 CSV 필수 컬럼이 없습니다: {missing_columns}")

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
    """NaN과 None을 빈 문자열로 정리합니다."""
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()

