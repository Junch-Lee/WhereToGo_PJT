'''
step 4. seed 및 정규화 데이터셋을 활용해 키워드 매칭 기준을 설정

- 1. 기존의 seed와 일치하는 경우 : topics 매칭 자동화
- 2. 지나치게 짧거나 긴 키워드 : 매칭되더라도 topics 후보로 분류
- 3. (learning_resources) 키워드 X : title, description 필드 참고하여 키워드 후보 추출

'''

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
SEED_DIR = PROJECT_ROOT / "curriculum-data" / "seed"
PIPELINE_DATA_DIR = SCRIPT_DIR / "data"
PROCESSED_DIR = PIPELINE_DATA_DIR / "processed"
KEYWORDS_DIR = PIPELINE_DATA_DIR / "keywords"
TOPIC_OUTPUT_DIR = PIPELINE_DATA_DIR / "topic_matches"


# -----------------------------------------------------------------------------
# Field score policy
# -----------------------------------------------------------------------------

COURSE_FIELD_SCORES = {
    "course_name_clean": {
        "topic_name": 0.95,
        "alias": 0.90,
        "depth3_candidate": 0.85,
    },
    "learning_objective_clean": {
        "topic_name": 0.80,
        "alias": 0.75,
        "depth3_candidate": 0.80,
    },
    "prerequisite_material_clean": {
        "topic_name": 0.68,
        "alias": 0.65,
        "depth3_candidate": 0.65,
    },
    "main_textbook_clean": {
        "topic_name": 0.50,
        "alias": 0.50,
        "depth3_candidate": None,
    },
}

RESOURCE_FIELD_SCORES:dict[str, dict[str, float | None]] = {
    "title_clean": {
        "topic_name": 0.95,
        "alias": 0.90,
        "depth3_candidate": 0.85,
    },
    "description_keyword_items": {
        "topic_name": 0.88,
        "alias": 0.85,
        "depth3_candidate": 0.88,
    },
    "description_keywords_raw": {
        "topic_name": 0.85,
        "alias": 0.82,
        "depth3_candidate": 0.85,
    },
    "description_body_clean": {
        "topic_name": 0.80,
        "alias": 0.75,
        "depth3_candidate": 0.80,
    },
}

IT_SUB_CATEGORIES = {
    "컴퓨터공학",
    "컴퓨터과학",
    "소프트웨어공학",
    "정보통신공학",
    "인공지능",
    "데이터사이언스",
}


# -----------------------------------------------------------------------------
# Basic utils
# -----------------------------------------------------------------------------

INVISIBLE_CHARS_PATTERN = re.compile(r"[\u200b\u200c\u200d\ufeff\u00a0]")
MULTI_SPACE_PATTERN = re.compile(r"\s+")


def read_csv_safely(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="cp949")

    df.columns = [col.strip() for col in df.columns]

    for col in df.columns:
        df[col] = df[col].astype(str)

    return df


def normalize_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value)
    text = unicodedata.normalize("NFKC", text)
    text = INVISIBLE_CHARS_PATTERN.sub(" ", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
    text = MULTI_SPACE_PATTERN.sub(" ", text)
    return text.strip()


def normalize_for_match(value: Any) -> str:
    return normalize_text(value).lower()


def is_ascii_like(text: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9#+/\-_. ]+", text))


def contains_term(text: str, term: str) -> bool:
    """
    contains 매칭.

    - 영문/기호 중심 term은 간단한 ASCII boundary를 적용한다.
      예: java는 javascript 안에서 매칭되지 않음.
    - 한글 term은 일반 substring 매칭을 사용한다.
    """
    text_norm = normalize_for_match(text)
    term_norm = normalize_for_match(term)

    if not text_norm or not term_norm:
        return False

    if is_ascii_like(term_norm):
        pattern = (
            r"(?<![A-Za-z0-9])"
            + re.escape(term_norm)
            + r"(?![A-Za-z0-9])"
        )
        return re.search(pattern, text_norm) is not None

    return term_norm in text_norm


def matches_by_policy(text: str, term: str, policy: str) -> bool:
    text_norm = normalize_for_match(text)
    term_norm = normalize_for_match(term)

    if not text_norm or not term_norm:
        return False

    if policy == "exact":
        return text_norm == term_norm

    if policy == "normalized_exact":
        return text_norm == term_norm

    if policy == "contains":
        return contains_term(text_norm, term_norm)

    return False


def short_contains_penalty(term: str, policy: str) -> float:
    if policy == "contains" and len(normalize_text(term)) <= 3:
        return -0.05
    return 0.0


def safe_json_list(value: str) -> list[str]:
    if not value:
        return []

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []

    if not isinstance(parsed, list):
        return []

    return [str(item) for item in parsed if str(item).strip()]


# -----------------------------------------------------------------------------
# Seed preparation
# -----------------------------------------------------------------------------

def prepare_topic_records(seed_topics: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for _, row in seed_topics.iterrows():
        if str(row.get("is_active", "")).lower() != "true":
            continue

        name = row.get("name", "")
        if not name:
            continue

        records.append(
            {
                "topic_slug": row.get("slug", ""),
                "topic_name": name,
                "topic_depth": row.get("depth", ""),
                "parent_slug": row.get("parent_slug", ""),
                "priority": row.get("priority", ""),
                "match_value": name,
                "match_policy": "contains",
            }
        )

    # 긴 이름 우선
    records.sort(key=lambda x: len(x["match_value"]), reverse=True)
    return records


def prepare_alias_records(
    seed_aliases: pd.DataFrame,
    topic_by_slug: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for _, row in seed_aliases.iterrows():
        topic_slug = row.get("topic_slug", "")
        topic = topic_by_slug.get(topic_slug)

        if not topic:
            continue

        alias_name = row.get("alias_name", "")
        if not alias_name:
            continue

        records.append(
            {
                "topic_slug": topic_slug,
                "topic_name": topic["name"],
                "topic_depth": topic["depth"],
                "parent_slug": topic["parent_slug"],
                "priority": row.get("priority", ""),
                "match_value": alias_name,
                "match_policy": row.get("match_policy", "contains"),
                "alias_name": alias_name,
            }
        )

    # 긴 alias 우선
    records.sort(key=lambda x: len(x["match_value"]), reverse=True)
    return records


def prepare_depth3_records(depth3_candidates: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for _, row in depth3_candidates.iterrows():
        candidate_name = row.get("candidate_name", "")
        if not candidate_name:
            continue

        terms = [candidate_name]

        aliases = row.get("aliases", "")
        if aliases:
            terms.extend([item.strip() for item in aliases.split("|") if item.strip()])

        for term in terms:
            records.append(
                {
                    "candidate_name": candidate_name,
                    "suggested_parent_slug": row.get("suggested_parent_slug", ""),
                    "suggested_depth": row.get("suggested_depth", "3"),
                    "priority": row.get("priority", ""),
                    "decision_hint": row.get("decision_hint", ""),
                    "match_value": term,
                    "match_policy": "contains",
                }
            )

    # 긴 후보 우선
    records.sort(key=lambda x: len(x["match_value"]), reverse=True)
    return records


# -----------------------------------------------------------------------------
# Matching
# -----------------------------------------------------------------------------

def match_existing_topics(
    text: str,
    source_field: str,
    source_scores: dict[str, dict[str, float | None]],
    topic_records: list[dict[str, Any]],
    alias_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []

    if not text:
        return matches

    # 1. topic name direct matching
    for topic in topic_records:
        score = source_scores.get(source_field, {}).get("topic_name")
        if score is None:
            continue

        if contains_term(text, topic["match_value"]):
            matches.append(
                {
                    "match_type": "topic_name",
                    "match_policy": "contains",
                    "matched_value": topic["match_value"],
                    "alias_name": "",
                    "topic_slug": topic["topic_slug"],
                    "topic_name": topic["topic_name"],
                    "topic_depth": topic["topic_depth"],
                    "parent_slug": topic["parent_slug"],
                    "priority": topic["priority"],
                    "base_score": score,
                    "adjustment_score": 0.0,
                    "is_existing_topic": True,
                    "needs_review": False,
                }
            )

    # 2. alias matching
    for alias in alias_records:
        score = source_scores.get(source_field, {}).get("alias")
        if score is None:
            continue

        policy = alias["match_policy"]
        alias_name = alias["match_value"]

        if matches_by_policy(text, alias_name, policy):
            penalty = short_contains_penalty(alias_name, policy)

            matches.append(
                {
                    "match_type": "alias",
                    "match_policy": policy,
                    "matched_value": alias_name,
                    "alias_name": alias_name,
                    "topic_slug": alias["topic_slug"],
                    "topic_name": alias["topic_name"],
                    "topic_depth": alias["topic_depth"],
                    "parent_slug": alias["parent_slug"],
                    "priority": alias["priority"],
                    "base_score": score,
                    "adjustment_score": penalty,
                    "is_existing_topic": True,
                    "needs_review": False,
                }
            )

    return matches


def match_depth3_candidates(
    text: str,
    source_field: str,
    source_scores: dict[str, dict[str, float | None]],
    depth3_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []

    if not text:
        return matches

    score = source_scores.get(source_field, {}).get("depth3_candidate")
    if score is None:
        return matches

    for candidate in depth3_records:
        term = candidate["match_value"]

        if contains_term(text, term):
            matches.append(
                {
                    "match_type": "depth3_candidate",
                    "match_policy": "contains",
                    "matched_value": term,
                    "alias_name": "",
                    "topic_slug": "",
                    "topic_name": "",
                    "topic_depth": "3",
                    "parent_slug": "",
                    "candidate_name": candidate["candidate_name"],
                    "suggested_parent_slug": candidate["suggested_parent_slug"],
                    "suggested_depth": candidate["suggested_depth"],
                    "priority": candidate["priority"],
                    "base_score": score,
                    "adjustment_score": 0.0,
                    "is_existing_topic": False,
                    "needs_review": True,
                }
            )

    return matches


def build_raw_match_row(
    *,
    source_dataset: str,
    source_id: str,
    source_row_index: int,
    source_title: str,
    source_field: str,
    matched_text: str,
    relation_hint: str,
    match: dict[str, Any],
    category_bonus: float = 0.0,
) -> dict[str, Any]:
    base_score = float(match.get("base_score", 0.0))
    adjustment_score = float(match.get("adjustment_score", 0.0)) + category_bonus
    final_score = min(max(base_score + adjustment_score, 0.0), 1.0)

    return {
        "source_dataset": source_dataset,
        "source_id": source_id,
        "source_row_index": source_row_index,
        "source_title": source_title,
        "source_field": source_field,
        "matched_text": matched_text,
        "matched_value": match.get("matched_value", ""),
        "match_type": match.get("match_type", ""),
        "match_policy": match.get("match_policy", ""),
        "topic_slug": match.get("topic_slug", ""),
        "topic_name": match.get("topic_name", ""),
        "topic_depth": match.get("topic_depth", ""),
        "parent_slug": match.get("parent_slug", ""),
        "alias_name": match.get("alias_name", ""),
        "candidate_name": match.get("candidate_name", ""),
        "suggested_parent_slug": match.get("suggested_parent_slug", ""),
        "suggested_depth": match.get("suggested_depth", ""),
        "base_score": round(base_score, 4),
        "adjustment_score": round(adjustment_score, 4),
        "final_score": round(final_score, 4),
        "relation_hint": relation_hint,
        "is_existing_topic": str(bool(match.get("is_existing_topic"))).lower(),
        "needs_review": str(bool(match.get("needs_review"))).lower(),
        "priority": match.get("priority", ""),
    }


def collect_raw_match_rows(
    *,
    text: str,
    source_dataset: str,
    source_id: str,
    source_row_index: int,
    source_title: str,
    source_field: str,
    source_scores: dict[str, dict[str, float | None]],
    topic_records: list[dict[str, Any]],
    alias_records: list[dict[str, Any]],
    depth3_records: list[dict[str, Any]],
    relation_hint: str = "",
    category_bonus: float = 0.0,
) -> list[dict[str, Any]]:
    normalized_text = normalize_text(text)
    if not normalized_text:
        return []

    matches = match_existing_topics(
        text=normalized_text,
        source_field=source_field,
        source_scores=source_scores,
        topic_records=topic_records,
        alias_records=alias_records,
    )
    matches += match_depth3_candidates(
        text=normalized_text,
        source_field=source_field,
        source_scores=source_scores,
        depth3_records=depth3_records,
    )

    return [
        build_raw_match_row(
            source_dataset=source_dataset,
            source_id=source_id,
            source_row_index=source_row_index,
            source_title=source_title,
            source_field=source_field,
            matched_text=normalized_text,
            relation_hint=relation_hint,
            match=match,
            category_bonus=category_bonus,
        )
        for match in matches
    ]


def match_course_rows(
    curriculum_df: pd.DataFrame,
    topic_records: list[dict[str, Any]],
    alias_records: list[dict[str, Any]],
    depth3_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    raw_rows: list[dict[str, Any]] = []

    for source_row_index, (idx, row) in enumerate(curriculum_df.iterrows()):
        source_id = row.get("source_row_number", str(idx))
        source_title = row.get("course_name", "")

        for field in COURSE_FIELD_SCORES:
            if field not in curriculum_df.columns:
                continue

            relation_hint = "prerequisite" if field == "prerequisite_material_clean" else ""
            raw_rows.extend(
                collect_raw_match_rows(
                    text=row.get(field, ""),
                    source_dataset="course",
                    source_id=source_id,
                    source_row_index=source_row_index,
                    source_title=source_title,
                    source_field=field,
                    source_scores=COURSE_FIELD_SCORES,
                    topic_records=topic_records,
                    alias_records=alias_records,
                    depth3_records=depth3_records,
                    relation_hint=relation_hint,
                )
            )

    return raw_rows


def match_resource_field(
    *,
    row: pd.Series,
    idx: int,
    field: str,
    text: str,
    category_bonus: float,
    topic_records: list[dict[str, Any]],
    alias_records: list[dict[str, Any]],
    depth3_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return collect_raw_match_rows(
        text=text,
        source_dataset="resource",
        source_id=row.get("external_id", str(idx)),
        source_row_index=idx,
        source_title=row.get("title", ""),
        source_field=field,
        source_scores=RESOURCE_FIELD_SCORES,
        topic_records=topic_records,
        alias_records=alias_records,
        depth3_records=depth3_records,
        category_bonus=category_bonus,
    )


def match_resource_rows(
    resources_df: pd.DataFrame,
    topic_records: list[dict[str, Any]],
    alias_records: list[dict[str, Any]],
    depth3_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    raw_rows: list[dict[str, Any]] = []

    normal_fields = [
        "title_clean",
        "description_keywords_raw",
        "description_body_clean",
    ]

    for source_row_index, (idx, row) in enumerate(resources_df.iterrows()):
        sub_category = row.get("sub_category", "")
        category_bonus = 0.02 if sub_category in IT_SUB_CATEGORIES else 0.0

        for field in normal_fields:
            if field not in resources_df.columns:
                continue

            raw_rows.extend(
                match_resource_field(
                    row=row,
                    idx=source_row_index,
                    field=field,
                    text=row.get(field, ""),
                    category_bonus=category_bonus,
                    topic_records=topic_records,
                    alias_records=alias_records,
                    depth3_records=depth3_records,
                )
            )

        for keyword in safe_json_list(row.get("description_keyword_items_json", "")):
            raw_rows.extend(
                match_resource_field(
                    row=row,
                    idx=source_row_index,
                    field="description_keyword_items",
                    text=keyword,
                    category_bonus=category_bonus,
                    topic_records=topic_records,
                    alias_records=alias_records,
                    depth3_records=depth3_records,
                )
            )

    return raw_rows


# -----------------------------------------------------------------------------
# Aggregation
# -----------------------------------------------------------------------------

def candidate_key(row: pd.Series) -> str:
    if row["is_existing_topic"] == "true":
        return f"topic::{row['topic_slug']}"

    return f"candidate::{row['candidate_name']}::{row['suggested_parent_slug']}"


def aggregate_matches(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty:
        return pd.DataFrame()

    df = raw_df.copy()
    df["candidate_key"] = df.apply(candidate_key, axis=1)

    grouped_rows: list[dict[str, Any]] = []

    group_cols = ["source_dataset", "source_id", "candidate_key"]

    for _, group in df.groupby(group_cols):
        first = group.iloc[0]

        matched_fields = sorted(set(group["source_field"].tolist()))
        match_types = sorted(set(group["match_type"].tolist()))
        relation_hints = sorted(
            hint for hint in set(group["relation_hint"].tolist()) if hint
        )

        max_score = float(group["final_score"].max())
        evidence_count = int(len(group))

        repeated_field_count = len(matched_fields)
        repeat_bonus = 0.0

        if repeated_field_count >= 3:
            repeat_bonus += 0.05
        elif repeated_field_count == 2:
            repeat_bonus += 0.03

        has_title_like = bool(
            {"title_clean", "course_name_clean"} & set(matched_fields)
        )
        has_detail_like = bool(
            {
                "description_keyword_items",
                "description_keywords_raw",
                "description_body_clean",
                "learning_objective_clean",
            }
            & set(matched_fields)
        )

        if has_title_like and has_detail_like:
            repeat_bonus += 0.05

        final_score = min(max_score + repeat_bonus, 1.0)

        only_main_textbook = matched_fields == ["main_textbook_clean"]
        only_prerequisite = matched_fields == ["prerequisite_material_clean"]

        is_existing_topic = first["is_existing_topic"] == "true"
        needs_review = first["needs_review"] == "true"

        is_auto_link_candidate = (
            is_existing_topic
            and not needs_review
            and not only_main_textbook
            and not only_prerequisite
            and final_score >= 0.85
        )

        grouped_rows.append(
            {
                "source_dataset": first["source_dataset"],
                "source_id": first["source_id"],
                "source_row_index": first["source_row_index"],
                "source_title": first["source_title"],
                "topic_slug": first["topic_slug"],
                "topic_name": first["topic_name"],
                "topic_depth": first["topic_depth"],
                "parent_slug": first["parent_slug"],
                "candidate_name": first["candidate_name"],
                "suggested_parent_slug": first["suggested_parent_slug"],
                "suggested_depth": first["suggested_depth"],
                "relevance_score": round(final_score, 4),
                "matched_fields": "|".join(matched_fields),
                "match_types": "|".join(match_types),
                "relation_hint": "|".join(relation_hints),
                "is_existing_topic": str(is_existing_topic).lower(),
                "needs_review": str(needs_review).lower(),
                "is_auto_link_candidate": str(is_auto_link_candidate).lower(),
                "evidence_count": evidence_count,
            }
        )

    return pd.DataFrame(grouped_rows)


def limit_candidates_per_source(aggregated_df: pd.DataFrame) -> pd.DataFrame:
    if aggregated_df.empty:
        return aggregated_df

    result_parts: list[pd.DataFrame] = []

    for source_dataset, dataset_df in aggregated_df.groupby("source_dataset"):
        for source_id, source_df in dataset_df.groupby("source_id"):
            normal_df = source_df[source_df["relation_hint"] != "prerequisite"]
            prereq_df = source_df[source_df["relation_hint"] == "prerequisite"]

            normal_df = normal_df.sort_values(
                by=["relevance_score", "evidence_count"],
                ascending=[False, False],
            ).head(8)

            if source_dataset == "course":
                prereq_df = prereq_df.sort_values(
                    by=["relevance_score", "evidence_count"],
                    ascending=[False, False],
                ).head(5)
            else:
                prereq_df = prereq_df.iloc[0:0]

            result_parts.append(pd.concat([normal_df, prereq_df], ignore_index=True))

    if not result_parts:
        return pd.DataFrame()

    return pd.concat(result_parts, ignore_index=True)


# -----------------------------------------------------------------------------
# Output shaping
# -----------------------------------------------------------------------------

def build_course_candidates(
    limited_df: pd.DataFrame,
    curriculum_df: pd.DataFrame,
) -> pd.DataFrame:
    course_df = limited_df[limited_df["source_dataset"] == "course"].copy()

    if course_df.empty:
        return pd.DataFrame()

    meta = curriculum_df.copy()
    meta["source_row_index"] = meta.index.astype(str)
    course_df["source_row_index"] = course_df["source_row_index"].astype(str)

    meta_cols = [
        "source_row_index",
        "source_row_number",
        "course_name",
        "department_name",
        "college_name",
    ]
    meta_cols = [col for col in meta_cols if col in meta.columns]

    course_df = course_df.merge(
        meta[meta_cols],
        on="source_row_index",
        how="left",
    )

    columns = [
        "source_row_number",
        "course_name",
        "department_name",
        "college_name",
        "topic_slug",
        "topic_name",
        "candidate_name",
        "suggested_parent_slug",
        "suggested_depth",
        "relevance_score",
        "matched_fields",
        "match_types",
        "relation_hint",
        "is_existing_topic",
        "needs_review",
        "is_auto_link_candidate",
        "evidence_count",
    ]

    return course_df[[col for col in columns if col in course_df.columns]]


def build_resource_candidates(
    limited_df: pd.DataFrame,
    resources_df: pd.DataFrame,
) -> pd.DataFrame:
    resource_df = limited_df[limited_df["source_dataset"] == "resource"].copy()

    if resource_df.empty:
        return pd.DataFrame()

    meta = resources_df.copy()
    meta["source_row_index"] = meta.index.astype(str)
    resource_df["source_row_index"] = resource_df["source_row_index"].astype(str)

    meta_cols = [
        "source_row_index",
        "external_id",
        "title",
        "provider_name",
        "main_category",
        "sub_category",
    ]
    meta_cols = [col for col in meta_cols if col in meta.columns]

    resource_df = resource_df.merge(
        meta[meta_cols],
        on="source_row_index",
        how="left",
    )

    columns = [
        "external_id",
        "title",
        "provider_name",
        "main_category",
        "sub_category",
        "topic_slug",
        "topic_name",
        "candidate_name",
        "suggested_parent_slug",
        "suggested_depth",
        "relevance_score",
        "matched_fields",
        "match_types",
        "is_existing_topic",
        "needs_review",
        "is_auto_link_candidate",
        "evidence_count",
    ]

    return resource_df[[col for col in columns if col in resource_df.columns]]


def build_report(
    raw_df: pd.DataFrame,
    limited_df: pd.DataFrame,
    curriculum_df: pd.DataFrame,
    resources_df: pd.DataFrame,
) -> dict[str, Any]:
    course_source_ids = set(curriculum_df.get("source_row_number", pd.Series(dtype=str)).astype(str))
    resource_source_ids = set(resources_df.get("external_id", pd.Series(dtype=str)).astype(str))

    matched_course_ids = set(
        limited_df[limited_df["source_dataset"] == "course"]["source_id"].astype(str)
    ) if not limited_df.empty else set()

    matched_resource_ids = set(
        limited_df[limited_df["source_dataset"] == "resource"]["source_id"].astype(str)
    ) if not limited_df.empty else set()

    top_matched_topics = {}
    top_depth3_candidates = {}

    if not limited_df.empty:
        existing_df = limited_df[
            (limited_df["is_existing_topic"] == "true")
            & (limited_df["topic_name"] != "")
        ]
        depth3_df = limited_df[
            (limited_df["needs_review"] == "true")
            & (limited_df["candidate_name"] != "")
        ]

        top_matched_topics = existing_df["topic_name"].value_counts().head(30).to_dict()
        top_depth3_candidates = depth3_df["candidate_name"].value_counts().head(30).to_dict()

    return {
        "status": "success",
        "course": {
            "total_rows": int(len(curriculum_df)),
            "matched_rows": int(len(matched_course_ids)),
            "unmatched_rows": int(max(len(course_source_ids) - len(matched_course_ids), 0)),
            "match_rate": round(len(matched_course_ids) / len(curriculum_df), 4)
            if len(curriculum_df) > 0 else 0.0,
        },
        "resource": {
            "total_rows": int(len(resources_df)),
            "matched_rows": int(len(matched_resource_ids)),
            "unmatched_rows": int(max(len(resource_source_ids) - len(matched_resource_ids), 0)),
            "match_rate": round(len(matched_resource_ids) / len(resources_df), 4)
            if len(resources_df) > 0 else 0.0,
        },
        "raw_match_records": int(len(raw_df)),
        "final_candidate_records": int(len(limited_df)),
        "auto_link_candidate_count": int(
            (limited_df["is_auto_link_candidate"] == "true").sum()
        ) if not limited_df.empty else 0,
        "needs_review_count": int(
            (limited_df["needs_review"] == "true").sum()
        ) if not limited_df.empty else 0,
        "field_match_counts": raw_df["source_field"].value_counts().to_dict()
        if not raw_df.empty else {},
        "match_type_counts": raw_df["match_type"].value_counts().to_dict()
        if not raw_df.empty else {},
        "top_matched_topics": top_matched_topics,
        "top_depth3_candidates": top_depth3_candidates,
    }


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Step 4 - Match seed topics, aliases, and depth3 candidates."
    )

    parser.add_argument(
        "--seed-topics",
        type=Path,
        default=SEED_DIR / "seed_topics_v0.2.csv",
    )
    parser.add_argument(
        "--seed-aliases",
        type=Path,
        default=SEED_DIR / "seed_aliases_v0.1.csv",
    )
    parser.add_argument(
        "--depth3-candidates",
        type=Path,
        default=SEED_DIR / "seed_depth3_candidate_terms_v0.1.csv",
    )
    parser.add_argument(
        "--curriculum",
        type=Path,
        default=PROCESSED_DIR / "curriculum_courses_normalized.csv",
    )
    parser.add_argument(
        "--resources",
        type=Path,
        default=KEYWORDS_DIR / "learning_resources_keywords_extracted.csv",
    )
    parser.add_argument(
        "--output-raw-matches",
        type=Path,
        default=TOPIC_OUTPUT_DIR / "topic_match_results.csv",
    )
    parser.add_argument(
        "--output-course-candidates",
        type=Path,
        default=TOPIC_OUTPUT_DIR / "course_topic_match_candidates.csv",
    )
    parser.add_argument(
        "--output-resource-candidates",
        type=Path,
        default=TOPIC_OUTPUT_DIR / "resource_topic_match_candidates.csv",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=TOPIC_OUTPUT_DIR / "topic_matching_report.json",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    args.output_raw_matches.parent.mkdir(parents=True, exist_ok=True)
    args.output_course_candidates.parent.mkdir(parents=True, exist_ok=True)
    args.output_resource_candidates.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.parent.mkdir(parents=True, exist_ok=True)

    seed_topics = read_csv_safely(args.seed_topics)
    seed_aliases = read_csv_safely(args.seed_aliases)
    depth3_candidates = read_csv_safely(args.depth3_candidates)
    curriculum_df = read_csv_safely(args.curriculum)
    resources_df = read_csv_safely(args.resources)

    topic_by_slug = {
        row["slug"]: {
            "name": row["name"],
            "depth": row["depth"],
            "parent_slug": row["parent_slug"],
            "priority": row["priority"],
        }
        for _, row in seed_topics.iterrows()
    }

    topic_records = prepare_topic_records(seed_topics)
    alias_records = prepare_alias_records(seed_aliases, topic_by_slug)
    depth3_records = prepare_depth3_records(depth3_candidates)

    course_raw_rows = match_course_rows(
        curriculum_df=curriculum_df,
        topic_records=topic_records,
        alias_records=alias_records,
        depth3_records=depth3_records,
    )

    resource_raw_rows = match_resource_rows(
        resources_df=resources_df,
        topic_records=topic_records,
        alias_records=alias_records,
        depth3_records=depth3_records,
    )

    raw_df = pd.DataFrame(course_raw_rows + resource_raw_rows)

    if raw_df.empty:
        raw_df = pd.DataFrame(
            columns=[
                "source_dataset",
                "source_id",
                "source_row_index",
                "source_title",
                "source_field",
                "matched_text",
                "matched_value",
                "match_type",
                "match_policy",
                "topic_slug",
                "topic_name",
                "topic_depth",
                "parent_slug",
                "alias_name",
                "candidate_name",
                "suggested_parent_slug",
                "suggested_depth",
                "base_score",
                "adjustment_score",
                "final_score",
                "relation_hint",
                "is_existing_topic",
                "needs_review",
                "priority",
            ]
        )

    aggregated_df = aggregate_matches(raw_df)
    limited_df = limit_candidates_per_source(aggregated_df)

    course_candidates = build_course_candidates(limited_df, curriculum_df)
    resource_candidates = build_resource_candidates(limited_df, resources_df)

    raw_df.to_csv(args.output_raw_matches, index=False, encoding="utf-8-sig")
    course_candidates.to_csv(args.output_course_candidates, index=False, encoding="utf-8-sig")
    resource_candidates.to_csv(args.output_resource_candidates, index=False, encoding="utf-8-sig")

    report = build_report(
        raw_df=raw_df,
        limited_df=limited_df,
        curriculum_df=curriculum_df,
        resources_df=resources_df,
    )

    with args.output_report.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("=" * 80)
    print("Topic Pipeline Step 4 - Match Seed Topics")
    print("=" * 80)
    print("Status: success")
    print(f"Raw matches output       : {args.output_raw_matches}")
    print(f"Course candidates output : {args.output_course_candidates}")
    print(f"Resource candidates output: {args.output_resource_candidates}")
    print(f"Report output            : {args.output_report}")

    print("\nSummary:")
    print(f"- raw_match_records        : {report['raw_match_records']}")
    print(f"- final_candidate_records  : {report['final_candidate_records']}")
    print(f"- auto_link_candidate_count: {report['auto_link_candidate_count']}")
    print(f"- needs_review_count       : {report['needs_review_count']}")

    print("\nCourse:")
    print(f"- total_rows    : {report['course']['total_rows']}")
    print(f"- matched_rows  : {report['course']['matched_rows']}")
    print(f"- unmatched_rows: {report['course']['unmatched_rows']}")
    print(f"- match_rate    : {report['course']['match_rate']}")

    print("\nResource:")
    print(f"- total_rows    : {report['resource']['total_rows']}")
    print(f"- matched_rows  : {report['resource']['matched_rows']}")
    print(f"- unmatched_rows: {report['resource']['unmatched_rows']}")
    print(f"- match_rate    : {report['resource']['match_rate']}")

    print("\nTop matched topics:")
    for topic, count in list(report["top_matched_topics"].items())[:15]:
        print(f"- {topic}: {count}")

    print("\nTop depth3 candidates:")
    for topic, count in list(report["top_depth3_candidates"].items())[:15]:
        print(f"- {topic}: {count}")


if __name__ == "__main__":
    main()
