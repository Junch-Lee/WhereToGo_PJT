"""CSV row를 ChromaDB에 적재할 문서 dict로 변환하는 모듈."""

from __future__ import annotations

import math

import pandas as pd

from typing import Any

def build_course_documents(courses_df: pd.DataFrame, topic_map: dict) -> list[dict]:
    """강의 CSV 데이터를 ChromaDB 문서 dict 목록으로 변환합니다.

    Args:
        courses_df: curriculum_courses.csv를 로드한 DataFrame입니다.
        topic_map: source_row_number를 키로 하는 토픽명 매핑 dict입니다.

    Returns:
        {"id": str, "text": str, "metadata": dict} 구조의 일반 dict 목록입니다.
    """
    documents: list[dict] = []
    for _, row in courses_df.iterrows():
        source_row_number = _to_int(row.get("source_row_number"))
        grade = _to_int(row.get("grade"))
        credit = _to_int(row.get("credit"))
        topic_names = _clean_text(topic_map.get(source_row_number, ""))
        prerequisite = _clean_text(row.get("prerequisite_material"))

        metadata = _clean_metadata(
            {
                "doc_type": "course",
                "source_row_number": source_row_number,
                "university_name": _clean_text(row.get("university_name")),
                "college_name": _clean_text(row.get("college_name")),
                "department_name": _clean_text(row.get("department_name")),
                "course_name": _clean_text(row.get("course_name")),
                "grade": grade,
                "semester": _clean_text(row.get("semester")),
                "credit": credit,
                "has_prerequisite": bool(prerequisite),
                "estimated_difficulty": _estimate_difficulty(grade),
                "topic_names": topic_names,
            }
        )
        documents.append(
            {
                "id": f"course_{source_row_number}",
                "text": _build_course_text(row, topic_names),
                "metadata": metadata,
            }
        )

    return documents


def build_resource_documents(resources_df: pd.DataFrame, topic_map: dict) -> list[dict]:
    """학습 자료 CSV 데이터를 ChromaDB 문서 dict 목록으로 변환합니다.

    Args:
        resources_df: learning_resource.csv를 로드한 DataFrame입니다.
        topic_map: external_id를 키로 하는 토픽명 매핑 dict입니다.

    Returns:
        {"id": str, "text": str, "metadata": dict} 구조의 일반 dict 목록입니다.
    """
    documents: list[dict] = []
    for _, row in resources_df.iterrows():
        source_type = _clean_text(row.get("source_type"))
        external_id = _clean_text(row.get("external_id"))
        topic_names = _clean_text(topic_map.get(external_id, ""))

        metadata = _clean_metadata(
            {
                "doc_type": "resource",
                "source_type": source_type,
                "external_id": external_id,
                "title": _clean_text(row.get("title")),
                "main_category": _clean_text(row.get("main_category")),
                "sub_category": _clean_text(row.get("sub_category")),
                "difficulty_level": _clean_text(row.get("difficulty_level")) or "unknown",
                "content_type": _clean_text(row.get("content_type")),
                "provider_name": _clean_text(row.get("provider_name")),
                "instructor_name": _clean_text(row.get("instructor_name")),
                "topic_names": topic_names,
            }
        )
        documents.append(
            {
                "id": f"resource_{source_type}_{external_id}",
                "text": _build_resource_text(row, topic_names),
                "metadata": metadata,
            }
        )

    return documents


def _build_course_text(row: pd.Series, topic_names: str) -> str:
    """강의 문서의 임베딩 대상 텍스트를 생성합니다."""
    lines = ["[대학 강의계획서]", ""]
    _append_line(lines, "과목명", row.get("course_name"))
    _append_line(lines, "학과", row.get("department_name"))

    grade = _to_int(row.get("grade"))
    semester = _clean_text(row.get("semester"))
    grade_semester = " ".join(part for part in [f"{grade}학년" if grade else "", semester] if part)
    _append_line(lines, "학년/학기", grade_semester)
    _append_line(lines, "학점", row.get("credit"))

    _append_section(lines, "학습 목표", row.get("learning_objective"))
    _append_section(lines, "선수 지식", row.get("prerequisite_material"))
    _append_section(lines, "주교재", row.get("main_textbook"))
    _append_section(lines, "연결 토픽", topic_names)
    return "\n".join(lines).strip()


def _build_resource_text(row: pd.Series, topic_names: str) -> str:
    """학습 자료 문서의 임베딩 대상 텍스트를 생성합니다."""
    lines = ["[학습 자료]", ""]
    _append_line(lines, "자료명", row.get("title"))

    main_category = _clean_text(row.get("main_category"))
    sub_category = _clean_text(row.get("sub_category"))
    category = " > ".join(part for part in [main_category, sub_category] if part)
    _append_line(lines, "분야", category)
    _append_line(lines, "난이도", row.get("difficulty_level"))
    _append_line(lines, "자료 유형", row.get("content_type"))
    _append_line(lines, "제공처", row.get("provider_name"))
    _append_line(lines, "교수자", row.get("instructor_name"))

    _append_section(lines, "설명", row.get("description"))
    _append_section(lines, "연결 토픽", topic_names)
    return "\n".join(lines).strip()


def _append_line(lines: list[str], label: str, value: object) -> None:
    """값이 있을 때만 한 줄 필드를 추가합니다."""
    text = _clean_text(value)
    if text:
        lines.append(f"{label}: {text}")


def _append_section(lines: list[str], label: str, value: object) -> None:
    """값이 있을 때만 여러 줄 섹션을 추가합니다."""
    text = _clean_text(value)
    if text:
        if lines and lines[-1] != "":
            lines.append("")
        lines.append(f"{label}:")
        lines.append(text)


def _clean_metadata(metadata: dict) -> dict:
    """ChromaDB가 허용하는 스칼라 타입만 남긴 metadata dict를 반환합니다."""
    cleaned: dict = {}
    for key, value in metadata.items():
        if value is None or isinstance(value, list):
            continue
        if isinstance(value, float) and math.isnan(value):
            continue
        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
    return cleaned


def _clean_text(value: Any) -> str:
    """NaN, None, 공백 문자열을 빈 문자열로 정리합니다."""
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _to_int(value: Any) -> int:
    """안전하게 int로 변환하고 실패 시 0을 반환합니다."""
    if value is None or pd.isna(value):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _estimate_difficulty(grade: int) -> str:
    """학년 기반 예상 난이도를 반환합니다."""
    if grade == 1:
        return "beginner"
    if grade == 2:
        return "intermediate"
    if grade >= 3:
        return "advanced"
    return "unknown"

