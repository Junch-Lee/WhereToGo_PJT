from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


COURSE_REQUIRED_COLUMNS = [
    "source_row_number",
    "course_name",
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
]

RESOURCE_REQUIRED_COLUMNS = [
    "external_id",
    "title",
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
]

APPROVED_REQUIRED_COLUMNS = [
    "slug",
    "name",
    "depth",
    "parent_slug",
    "topic_type",
    "priority",
    "is_active",
    "source_candidate_name",
    "occurrence_count",
    "max_relevance_score",
    "avg_relevance_score",
    "reviewer_note",
]

FINAL_TOPICS_COLUMNS = [
    "topic_slug",
    "parent_topic_slug",
    "name",
    "depth",
    "topic_type",
    "is_learning_unit",
    "is_assessable",
    "description",
    "is_active",
    "source_candidate_name",
    "occurrence_count",
    "max_relevance_score",
    "avg_relevance_score",
    "reviewer_note",
]

FINAL_COURSE_COLUMNS = [
    "curriculum_course_lookup_key",
    "course_name",
    "topic_lookup_key",
    "topic_name",
    "topic_depth",
    "parent_topic_slug",
    "relevance_score",
    "extraction_method",
    "is_primary",
    "matched_fields",
    "match_types",
    "link_type",
]

FINAL_RESOURCE_COLUMNS = [
    "learning_resource_lookup_key",
    "title",
    "topic_lookup_key",
    "topic_name",
    "topic_depth",
    "parent_topic_slug",
    "relevance_score",
    "extraction_method",
    "is_primary",
    "matched_fields",
    "match_types",
    "link_type",
]

EXCLUDED_COLUMNS = [
    "source_dataset",
    "source_lookup_key",
    "source_title",
    "candidate_name",
    "suggested_parent_slug",
    "topic_slug",
    "topic_name",
    "relevance_score",
    "exclusion_reason",
]

MIN_APPROVED_RELEVANCE = 0.70
MAX_TOPICS_PER_SOURCE = 8


def read_csv_safely(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Input CSV not found: {path}")

    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="cp949")

    df.columns = [str(col).strip() for col in df.columns]
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    return df


def validate_required_columns(df: pd.DataFrame, required_columns: list[str], label: str) -> None:
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"{label} missing required columns: {', '.join(missing)}")


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def parse_score(value: str) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return 0.0


def format_score(value: float) -> str:
    return f"{value:.2f}"


def contains_prerequisite(value: str) -> bool:
    return "prerequisite" in str(value).strip().lower()


def make_approved_lookup(approved_df: pd.DataFrame) -> dict[tuple[str, str], dict[str, str]]:
    lookup = {}
    for _, row in approved_df.iterrows():
        key = (row.get("source_candidate_name", ""), row.get("parent_slug", ""))
        lookup[key] = {
            "topic_slug": row.get("slug", ""),
            "topic_name": row.get("name", ""),
            "topic_depth": row.get("depth", ""),
            "parent_topic_slug": row.get("parent_slug", ""),
        }
    return lookup


def build_final_topics(approved_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in approved_df.iterrows():
        rows.append(
            {
                "topic_slug": row.get("slug", ""),
                "parent_topic_slug": row.get("parent_slug", ""),
                "name": row.get("name", ""),
                "depth": row.get("depth", ""),
                "topic_type": row.get("topic_type", "") or "concept",
                "is_learning_unit": "true",
                "is_assessable": "true",
                "description": row.get("reviewer_note", ""),
                "is_active": row.get("is_active", "") or "true",
                "source_candidate_name": row.get("source_candidate_name", ""),
                "occurrence_count": row.get("occurrence_count", ""),
                "max_relevance_score": row.get("max_relevance_score", ""),
                "avg_relevance_score": row.get("avg_relevance_score", ""),
                "reviewer_note": row.get("reviewer_note", ""),
            }
        )
    return pd.DataFrame(rows, columns=FINAL_TOPICS_COLUMNS)


def exclusion_row(row: pd.Series, dataset: str, lookup_key_col: str, title_col: str, reason: str) -> dict[str, str]:
    return {
        "source_dataset": dataset,
        "source_lookup_key": row.get(lookup_key_col, ""),
        "source_title": row.get(title_col, ""),
        "candidate_name": row.get("candidate_name", ""),
        "suggested_parent_slug": row.get("suggested_parent_slug", ""),
        "topic_slug": row.get("topic_slug", ""),
        "topic_name": row.get("topic_name", ""),
        "relevance_score": format_score(parse_score(row.get("relevance_score", ""))),
        "exclusion_reason": reason,
    }


def map_existing_topic(row: pd.Series) -> dict[str, str]:
    return {
        "topic_lookup_key": row.get("topic_slug", ""),
        "topic_name": row.get("topic_name", ""),
        "topic_depth": row.get("suggested_depth", ""),
        "parent_topic_slug": row.get("suggested_parent_slug", ""),
        "link_type": "existing_topic",
    }


def map_approved_topic(row: pd.Series, approved_lookup: dict[tuple[str, str], dict[str, str]]) -> dict[str, str]:
    key = (row.get("candidate_name", ""), row.get("suggested_parent_slug", ""))
    approved_topic = approved_lookup[key]
    return {
        "topic_lookup_key": approved_topic["topic_slug"],
        "topic_name": approved_topic["topic_name"],
        "topic_depth": approved_topic["topic_depth"],
        "parent_topic_slug": approved_topic["parent_topic_slug"],
        "link_type": "approved_depth3",
    }


def should_include_existing(row: pd.Series, is_course: bool) -> bool:
    if not parse_bool(row.get("is_existing_topic", "")):
        return False
    if not parse_bool(row.get("is_auto_link_candidate", "")):
        return False
    if row.get("topic_slug", "") == "":
        return False
    if is_course and contains_prerequisite(row.get("relation_hint", "")):
        return False
    return True


def build_link_rows(
    df: pd.DataFrame,
    approved_lookup: dict[tuple[str, str], dict[str, str]],
    dataset: str,
    lookup_key_col: str,
    title_col: str,
    output_columns: list[str],
    is_course: bool,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    link_rows = []
    excluded_rows = []

    for _, row in df.iterrows():
        score = parse_score(row.get("relevance_score", ""))
        approved_key = (row.get("candidate_name", ""), row.get("suggested_parent_slug", ""))
        topic_info = None
        reason = ""

        if should_include_existing(row, is_course):
            topic_info = map_existing_topic(row)
        elif parse_bool(row.get("needs_review", "")):
            if approved_key not in approved_lookup:
                reason = "review_candidate_not_approved"
            elif score < MIN_APPROVED_RELEVANCE:
                reason = "approved_depth3_relevance_below_threshold"
            else:
                topic_info = map_approved_topic(row, approved_lookup)
        elif is_course and contains_prerequisite(row.get("relation_hint", "")):
            reason = "course_prerequisite_relation_excluded"
        elif parse_bool(row.get("is_existing_topic", "")) and not parse_bool(row.get("is_auto_link_candidate", "")):
            reason = "existing_topic_not_auto_link_candidate"
        elif row.get("topic_slug", "") == "":
            reason = "missing_topic_slug"
        else:
            reason = "not_final_link_candidate"

        if topic_info is None:
            excluded_rows.append(exclusion_row(row, dataset, lookup_key_col, title_col, reason))
            continue

        link_row = {
            output_columns[0]: row.get(lookup_key_col, ""),
            output_columns[1]: row.get(title_col, ""),
            "topic_lookup_key": topic_info["topic_lookup_key"],
            "topic_name": topic_info["topic_name"],
            "topic_depth": topic_info["topic_depth"],
            "parent_topic_slug": topic_info["parent_topic_slug"],
            "relevance_score": format_score(score),
            "extraction_method": "keyword",
            "is_primary": "false",
            "matched_fields": row.get("matched_fields", ""),
            "match_types": row.get("match_types", ""),
            "link_type": topic_info["link_type"],
            "_score": score,
        }
        link_rows.append(link_row)

    links_df = pd.DataFrame(link_rows)
    if links_df.empty:
        return pd.DataFrame(columns=output_columns), pd.DataFrame(excluded_rows, columns=EXCLUDED_COLUMNS)

    links_df = finalize_links(links_df, output_columns[0], output_columns)
    return links_df, pd.DataFrame(excluded_rows, columns=EXCLUDED_COLUMNS)


def finalize_links(links_df: pd.DataFrame, source_key_col: str, output_columns: list[str]) -> pd.DataFrame:
    links_df = links_df.sort_values(
        by=[source_key_col, "topic_lookup_key", "_score"],
        ascending=[True, True, False],
        kind="mergesort",
    )
    links_df = links_df.drop_duplicates(subset=[source_key_col, "topic_lookup_key"], keep="first")

    links_df = links_df.sort_values(
        by=[source_key_col, "_score", "link_type"],
        ascending=[True, False, True],
        kind="mergesort",
    )
    links_df = links_df.groupby(source_key_col, sort=False).head(MAX_TOPICS_PER_SOURCE).copy()
    links_df["is_primary"] = "false"

    primary_indexes = links_df.groupby(source_key_col, sort=False).head(1).index
    links_df.loc[primary_indexes, "is_primary"] = "true"

    links_df = links_df.sort_values(
        by=[source_key_col, "is_primary", "_score"],
        ascending=[True, False, False],
        kind="mergesort",
    )
    return links_df[output_columns].reset_index(drop=True)


def build_report(
    course_df: pd.DataFrame,
    resource_df: pd.DataFrame,
    approved_df: pd.DataFrame,
    final_topics: pd.DataFrame,
    final_course_links: pd.DataFrame,
    final_resource_links: pd.DataFrame,
    excluded: pd.DataFrame,
    warnings: list[str],
) -> dict:
    all_links = pd.concat([final_course_links, final_resource_links], ignore_index=True)
    top_topics = {}
    if not all_links.empty:
        top_topics = all_links["topic_name"].value_counts().head(10).to_dict()

    existing_topic_links = 0
    approved_depth3_links = 0
    if not all_links.empty:
        existing_topic_links = int((all_links["link_type"] == "existing_topic").sum())
        approved_depth3_links = int((all_links["link_type"] == "approved_depth3").sum())

    return {
        "status": "success",
        "inputs": {
            "course_candidates": int(len(course_df)),
            "resource_candidates": int(len(resource_df)),
            "approved_depth3_topics": int(len(approved_df)),
        },
        "outputs": {
            "final_topics_depth3": int(len(final_topics)),
            "final_course_topic_links": int(len(final_course_links)),
            "final_resource_topic_links": int(len(final_resource_links)),
            "excluded_topic_link_candidates": int(len(excluded)),
        },
        "summary": {
            "course_linked_rows": int(len(final_course_links)),
            "resource_linked_rows": int(len(final_resource_links)),
            "existing_topic_links": existing_topic_links,
            "approved_depth3_links": approved_depth3_links,
            "primary_course_links": int((final_course_links["is_primary"] == "true").sum()) if not final_course_links.empty else 0,
            "primary_resource_links": int((final_resource_links["is_primary"] == "true").sum()) if not final_resource_links.empty else 0,
        },
        "top_topics": top_topics,
        "warnings": warnings,
    }


def write_outputs(
    output_dir: Path,
    final_topics: pd.DataFrame,
    final_course_links: pd.DataFrame,
    final_resource_links: pd.DataFrame,
    excluded: pd.DataFrame,
    report: dict,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    final_topics.to_csv(output_dir / "final_topics_depth3_import.csv", index=False, encoding="utf-8-sig")
    final_course_links.to_csv(output_dir / "final_course_topics_import.csv", index=False, encoding="utf-8-sig")
    final_resource_links.to_csv(output_dir / "final_resource_topics_import.csv", index=False, encoding="utf-8-sig")
    excluded.to_csv(output_dir / "excluded_topic_link_candidates.csv", index=False, encoding="utf-8-sig")

    with (output_dir / "final_topic_link_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def print_summary(report: dict, output_dir: Path) -> None:
    print("Status:", report["status"])
    print("input row counts:")
    print("- course_candidates:", report["inputs"]["course_candidates"])
    print("- resource_candidates:", report["inputs"]["resource_candidates"])
    print("- approved_depth3_topics:", report["inputs"]["approved_depth3_topics"])
    print("final depth3 topic count:", report["outputs"]["final_topics_depth3"])
    print("final course topic link count:", report["outputs"]["final_course_topic_links"])
    print("final resource topic link count:", report["outputs"]["final_resource_topic_links"])
    print("excluded candidate count:", report["outputs"]["excluded_topic_link_candidates"])
    print("existing_topic_links count:", report["summary"]["existing_topic_links"])
    print("approved_depth3_links count:", report["summary"]["approved_depth3_links"])
    print("output directory:", output_dir)
    print("warnings count:", len(report["warnings"]))
    print("top 10 topics:")
    if not report["top_topics"]:
        print("- none")
        return
    for topic_name, count in report["top_topics"].items():
        print(f"- {topic_name}: {count}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Step 07 - Build natural-key CSV exports for ERD import."
    )
    parser.add_argument(
        "--course-candidates",
        type=Path,
        default=Path("scripts/topic_pipeline/data/topic_matches/course_topic_match_candidates.csv"),
        help="Path to course topic match candidates CSV.",
    )
    parser.add_argument(
        "--resource-candidates",
        type=Path,
        default=Path("scripts/topic_pipeline/data/topic_matches/resource_topic_match_candidates.csv"),
        help="Path to resource topic match candidates CSV.",
    )
    parser.add_argument(
        "--approved-depth3",
        type=Path,
        default=Path("scripts/topic_pipeline/data/topic_candidates/approved_depth3_topics.csv"),
        help="Path to approved depth3 topics CSV.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("scripts/topic_pipeline/data/final"),
        help="Directory for final import CSV outputs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    warnings = []

    course_df = read_csv_safely(args.course_candidates)
    resource_df = read_csv_safely(args.resource_candidates)
    approved_df = read_csv_safely(args.approved_depth3)

    validate_required_columns(course_df, COURSE_REQUIRED_COLUMNS, "course_topic_match_candidates.csv")
    validate_required_columns(resource_df, RESOURCE_REQUIRED_COLUMNS, "resource_topic_match_candidates.csv")
    validate_required_columns(approved_df, APPROVED_REQUIRED_COLUMNS, "approved_depth3_topics.csv")

    approved_lookup = make_approved_lookup(approved_df)
    if len(approved_lookup) != len(approved_df):
        warnings.append("duplicate approved depth3 mapping keys found; later rows were used")

    final_topics = build_final_topics(approved_df)
    final_course_links, excluded_course = build_link_rows(
        course_df,
        approved_lookup,
        "course",
        "source_row_number",
        "course_name",
        FINAL_COURSE_COLUMNS,
        True,
    )
    final_resource_links, excluded_resource = build_link_rows(
        resource_df,
        approved_lookup,
        "resource",
        "external_id",
        "title",
        FINAL_RESOURCE_COLUMNS,
        False,
    )
    excluded = pd.concat([excluded_course, excluded_resource], ignore_index=True)
    if excluded.empty:
        excluded = pd.DataFrame(columns=EXCLUDED_COLUMNS)

    report = build_report(
        course_df,
        resource_df,
        approved_df,
        final_topics,
        final_course_links,
        final_resource_links,
        excluded,
        warnings,
    )
    write_outputs(args.output_dir, final_topics, final_course_links, final_resource_links, excluded, report)
    print_summary(report, args.output_dir)


if __name__ == "__main__":
    main()
