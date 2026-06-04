from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


REVIEW_COLUMNS = [
    "candidate_name",
    "suggested_parent_slug",
    "suggested_depth",
    "occurrence_count",
    "course_occurrence_count",
    "resource_occurrence_count",
    "max_relevance_score",
    "avg_relevance_score",
    "matched_source_titles",
    "matched_fields",
    "match_types",
    "decision",
    "merge_target_topic_slug",
    "reviewer_note",
]


def read_csv_safely(path: Path) -> pd.DataFrame:
    """Read CSV as strings while preserving Korean text encodings."""
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    try:
        df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(path, dtype=str, encoding="cp949")

    df.columns = [str(col).strip() for col in df.columns]
    return df.fillna("").astype(str)


def require_columns(df: pd.DataFrame, required_columns: list[str], path: Path) -> None:
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Missing required columns in {path}: {missing_text}")


def build_empty_source_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "candidate_name",
            "suggested_parent_slug",
            "suggested_depth",
            "relevance_score",
            "matched_fields",
            "match_types",
            "needs_review",
            "source_type",
            "source_title",
        ]
    )


def filter_review_rows(df: pd.DataFrame, source_type: str, title_column: str) -> pd.DataFrame:
    """Keep only depth3 candidate rows that need human review."""
    if df.empty:
        return build_empty_source_frame()

    required_columns = [
        "candidate_name",
        "suggested_parent_slug",
        "suggested_depth",
        "relevance_score",
        "matched_fields",
        "match_types",
        "needs_review",
        title_column,
    ]
    require_columns(df, required_columns, Path(f"{source_type} candidates"))

    review_df = df.copy()
    review_df["candidate_name"] = review_df["candidate_name"].str.strip()
    review_df["suggested_parent_slug"] = review_df["suggested_parent_slug"].str.strip()
    review_df["needs_review"] = review_df["needs_review"].str.strip().str.lower()

    review_df = review_df[
        (review_df["needs_review"] == "true")
        & (review_df["candidate_name"] != "")
        & (review_df["suggested_parent_slug"] != "")
    ].copy()

    review_df["source_type"] = source_type
    review_df["source_title"] = review_df[title_column].astype(str).str.strip()
    return review_df


def split_unique_values(values: pd.Series) -> list[str]:
    """Split pipe-delimited cells and return unique non-empty values in first-seen order."""
    unique_values = []
    seen = set()

    for value in values.astype(str):
        for item in value.split("|"):
            normalized = item.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique_values.append(normalized)

    return unique_values


def unique_join(values: pd.Series, separator: str, limit: int | None = None) -> str:
    unique_values = split_unique_values(values)
    if limit is not None:
        unique_values = unique_values[:limit]
    return separator.join(unique_values)


def first_non_empty(values: pd.Series, default: str = "") -> str:
    for value in values.astype(str):
        value = value.strip()
        if value:
            return value
    return default


def format_score(value: float) -> str:
    if pd.isna(value):
        return "0.0000"
    return f"{float(value):.4f}"


def aggregate_candidates(course_review_df: pd.DataFrame, resource_review_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate source-row candidates into a unique candidate review list."""
    combined_df = pd.concat([course_review_df, resource_review_df], ignore_index=True)

    if combined_df.empty:
        return pd.DataFrame(columns=REVIEW_COLUMNS)

    combined_df["relevance_score_number"] = pd.to_numeric(
        combined_df["relevance_score"],
        errors="coerce",
    )

    rows = []
    group_cols = ["candidate_name", "suggested_parent_slug"]

    for (candidate_name, suggested_parent_slug), group in combined_df.groupby(group_cols, sort=False):
        course_count = int((group["source_type"] == "course").sum())
        resource_count = int((group["source_type"] == "resource").sum())

        rows.append(
            {
                "candidate_name": candidate_name,
                "suggested_parent_slug": suggested_parent_slug,
                "suggested_depth": first_non_empty(group["suggested_depth"], "3"),
                "occurrence_count": int(len(group)),
                "course_occurrence_count": course_count,
                "resource_occurrence_count": resource_count,
                "max_relevance_score": format_score(group["relevance_score_number"].max()),
                "avg_relevance_score": format_score(group["relevance_score_number"].mean()),
                "matched_source_titles": unique_join(group["source_title"], " | ", limit=5),
                "matched_fields": unique_join(group["matched_fields"], "|"),
                "match_types": unique_join(group["match_types"], "|"),
                "decision": "pending",
                "merge_target_topic_slug": "",
                "reviewer_note": "",
            }
        )

    review_df = pd.DataFrame(rows, columns=REVIEW_COLUMNS)
    return sort_review_df(review_df)


def sort_review_df(review_df: pd.DataFrame) -> pd.DataFrame:
    if review_df.empty:
        return review_df

    sorted_df = review_df.copy()
    sorted_df["_max_score_sort"] = pd.to_numeric(sorted_df["max_relevance_score"], errors="coerce").fillna(0)
    sorted_df = sorted_df.sort_values(
        by=[
            "occurrence_count",
            "_max_score_sort",
            "suggested_parent_slug",
            "candidate_name",
        ],
        ascending=[False, False, True, True],
        kind="mergesort",
    )
    return sorted_df.drop(columns=["_max_score_sort"]).reset_index(drop=True)


def build_report(
    course_candidate_rows: int,
    resource_candidate_rows: int,
    course_review_rows: int,
    resource_review_rows: int,
    review_df: pd.DataFrame,
) -> dict[str, Any]:
    unique_candidate_count = int(len(review_df))
    total_occurrence_count = int(review_df["occurrence_count"].sum()) if not review_df.empty else 0

    if review_df.empty:
        top_candidates = {}
        parent_counts = {}
        distribution = {"course_only": 0, "resource_only": 0, "both": 0}
    else:
        top_candidates = (
            review_df.groupby("candidate_name")["occurrence_count"]
            .sum()
            .sort_values(ascending=False)
            .head(30)
            .astype(int)
            .to_dict()
        )
        parent_counts = (
            review_df["suggested_parent_slug"]
            .value_counts(sort=True)
            .astype(int)
            .to_dict()
        )
        distribution = {
            "course_only": int(
                ((review_df["course_occurrence_count"] > 0) & (review_df["resource_occurrence_count"] == 0)).sum()
            ),
            "resource_only": int(
                ((review_df["course_occurrence_count"] == 0) & (review_df["resource_occurrence_count"] > 0)).sum()
            ),
            "both": int(
                ((review_df["course_occurrence_count"] > 0) & (review_df["resource_occurrence_count"] > 0)).sum()
            ),
        }

    return {
        "status": "success",
        "input": {
            "course_candidate_rows": course_candidate_rows,
            "resource_candidate_rows": resource_candidate_rows,
            "course_review_rows": course_review_rows,
            "resource_review_rows": resource_review_rows,
        },
        "output": {
            "unique_candidate_count": unique_candidate_count,
            "total_occurrence_count": total_occurrence_count,
        },
        "summary": {
            "top_candidates": top_candidates,
            "parent_counts": parent_counts,
            "course_resource_distribution": distribution,
        },
    }


def write_outputs(review_df: pd.DataFrame, report: dict[str, Any], output_review: Path, output_report: Path) -> None:
    output_review.parent.mkdir(parents=True, exist_ok=True)
    output_report.parent.mkdir(parents=True, exist_ok=True)

    review_df.to_csv(output_review, index=False, encoding="utf-8-sig")
    with output_report.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def print_summary(report: dict[str, Any], output_review: Path, output_report: Path) -> None:
    print("Status:", report["status"])
    print("course candidate rows:", report["input"]["course_candidate_rows"])
    print("resource candidate rows:", report["input"]["resource_candidate_rows"])
    print("course review rows:", report["input"]["course_review_rows"])
    print("resource review rows:", report["input"]["resource_review_rows"])
    print("unique candidate count:", report["output"]["unique_candidate_count"])
    print("total occurrence count:", report["output"]["total_occurrence_count"])
    print("output csv path:", output_review)
    print("output report path:", output_report)
    print("top 10 candidates:")
    for candidate_name, count in list(report["summary"]["top_candidates"].items())[:10]:
        print(f"- {candidate_name}: {count}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Step 05 - Build a unique topic candidate review CSV."
    )
    parser.add_argument(
        "--course-candidates",
        type=Path,
        default=Path("scripts/topic_pipeline/data/topic_matches/course_topic_match_candidates.csv"),
        help="Path to Step 04 course topic match candidates CSV.",
    )
    parser.add_argument(
        "--resource-candidates",
        type=Path,
        default=Path("scripts/topic_pipeline/data/topic_matches/resource_topic_match_candidates.csv"),
        help="Path to Step 04 resource topic match candidates CSV.",
    )
    parser.add_argument(
        "--output-review",
        type=Path,
        default=Path("scripts/topic_pipeline/review/topic_candidates_review.csv"),
        help="Output path for the candidate review CSV.",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=Path("scripts/topic_pipeline/review/topic_candidates_review_report.json"),
        help="Output path for the review report JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    course_candidates = read_csv_safely(args.course_candidates)
    resource_candidates = read_csv_safely(args.resource_candidates)

    course_review = filter_review_rows(course_candidates, source_type="course", title_column="course_name")
    resource_review = filter_review_rows(resource_candidates, source_type="resource", title_column="title")

    review_df = aggregate_candidates(course_review, resource_review)
    report = build_report(
        course_candidate_rows=int(len(course_candidates)),
        resource_candidate_rows=int(len(resource_candidates)),
        course_review_rows=int(len(course_review)),
        resource_review_rows=int(len(resource_review)),
        review_df=review_df,
    )

    write_outputs(review_df, report, args.output_review, args.output_report)
    print_summary(report, args.output_review, args.output_report)


if __name__ == "__main__":
    main()
