from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "curriculum-data"
SEED_DIR = DATA_ROOT / "seed"
RAW_DIR = DATA_ROOT / "raw"
PROCESSED_DIR = DATA_ROOT / "processed" / "topic_pipeline"
DEFAULT_CURRICULUM_PATH = (
    RAW_DIR
    / "university_syllabus"
    / "data"
    / "university_syllabus_eda_cleaned_final.csv"
)
DEFAULT_LEARNING_RESOURCES_PATH = (
    RAW_DIR / "learning_resources" / "learning_resource_refactor.csv"
)


SEED_TOPICS_REQUIRED_COLUMNS = [
    "slug",
    "name",
    "depth",
    "parent_slug",
    "topic_type",
    "priority",
    "is_active",
    "note",
]

SEED_ALIASES_REQUIRED_COLUMNS = [
    "topic_slug",
    "alias_name",
    "language",
    "alias_type",
    "match_policy",
    "priority",
    "note",
]

DEPTH3_CANDIDATES_REQUIRED_COLUMNS = [
    "candidate_name",
    "suggested_parent_slug",
    "suggested_depth",
    "priority",
    "aliases",
    "decision_hint",
    "note",
]

CURRICULUM_REQUIRED_COLUMNS = [
    "source_row_number",
    "course_name",
    "learning_objective",
    "prerequisite_material",
    "main_textbook",
    "reference_material",
]

LEARNING_RESOURCE_REQUIRED_COLUMNS = [
    "source_type",
    "external_id",
    "title",
    "description",
]


def read_csv_safely(
    path: Path,
    empty_columns: list[str] | None = None,
) -> pd.DataFrame:
    """
    CSV를 안전하게 읽는다.
    - UTF-8 BOM 대응을 위해 utf-8-sig 우선 사용
    - 실패 시 cp949 fallback
    - 모든 값을 문자열로 읽음
    - NaN 대신 빈 문자열 사용
    """
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except EmptyDataError:
        if empty_columns is None:
            raise ValueError(f"CSV file is empty and has no header: {path}") from None
        df = pd.DataFrame(columns=empty_columns)
    except UnicodeDecodeError:
        df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="cp949")

    df.columns = [col.strip() for col in df.columns]

    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    return df


def check_required_columns(
    df: pd.DataFrame,
    required_columns: list[str],
    dataset_name: str,
) -> list[str]:
    errors: list[str] = []

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        errors.append(
            f"[{dataset_name}] Missing required columns: {', '.join(missing)}"
        )

    return errors


def validate_seed_topics(seed_topics: pd.DataFrame) -> list[str]:
    errors: list[str] = []

    errors.extend(
        check_required_columns(
            seed_topics,
            SEED_TOPICS_REQUIRED_COLUMNS,
            "seed_topics",
        )
    )

    if errors:
        return errors

    if seed_topics.empty:
        errors.append("[seed_topics] File is empty.")
        return errors

    duplicated_slugs = (
        seed_topics[seed_topics["slug"].duplicated(keep=False)]["slug"]
        .unique()
        .tolist()
    )
    if duplicated_slugs:
        errors.append(
            f"[seed_topics] Duplicate slug values: {', '.join(duplicated_slugs)}"
        )

    valid_depths = {"1", "2", "3"}
    invalid_depth_rows = seed_topics[~seed_topics["depth"].isin(valid_depths)]
    if not invalid_depth_rows.empty:
        errors.append(
            "[seed_topics] depth must be one of 1, 2, 3. "
            f"Invalid rows: {invalid_depth_rows[['slug', 'name', 'depth']].to_dict(orient='records')}"
        )

    # 현재 seed_topics_v0.2는 depth 1~2만 들어가는 것을 권장했지만,
    # 검증 로직은 추후 depth 3 seed가 들어와도 깨지지 않도록 3까지 허용한다.
    slug_set = set(seed_topics["slug"].tolist())

    depth1 = seed_topics[seed_topics["depth"] == "1"]
    depth2_or_3 = seed_topics[seed_topics["depth"].isin(["2", "3"])]

    invalid_depth1_parent = depth1[depth1["parent_slug"] != ""]
    if not invalid_depth1_parent.empty:
        errors.append(
            "[seed_topics] depth=1 topics must have empty parent_slug. "
            f"Invalid rows: {invalid_depth1_parent[['slug', 'name', 'parent_slug']].to_dict(orient='records')}"
        )

    missing_parent_rows = depth2_or_3[
        ~depth2_or_3["parent_slug"].isin(slug_set)
    ]
    if not missing_parent_rows.empty:
        errors.append(
            "[seed_topics] depth=2 or depth=3 topics must have valid parent_slug. "
            f"Invalid rows: {missing_parent_rows[['slug', 'name', 'parent_slug']].to_dict(orient='records')}"
        )

    valid_topic_types = {"domain", "subject", "concept", "skill"}
    invalid_topic_type_rows = seed_topics[
        ~seed_topics["topic_type"].isin(valid_topic_types)
    ]
    if not invalid_topic_type_rows.empty:
        errors.append(
            "[seed_topics] Invalid topic_type. "
            f"Allowed: {', '.join(sorted(valid_topic_types))}. "
            f"Invalid rows: {invalid_topic_type_rows[['slug', 'name', 'topic_type']].to_dict(orient='records')}"
        )

    valid_priorities = {"P0", "P1", "P2", "P3"}
    invalid_priority_rows = seed_topics[
        ~seed_topics["priority"].isin(valid_priorities)
    ]
    if not invalid_priority_rows.empty:
        errors.append(
            "[seed_topics] Invalid priority. "
            f"Allowed: {', '.join(sorted(valid_priorities))}. "
            f"Invalid rows: {invalid_priority_rows[['slug', 'name', 'priority']].to_dict(orient='records')}"
        )

    valid_active_values = {"true", "false", "True", "False", "TRUE", "FALSE"}
    invalid_active_rows = seed_topics[
        ~seed_topics["is_active"].isin(valid_active_values)
    ]
    if not invalid_active_rows.empty:
        errors.append(
            "[seed_topics] is_active must be true or false. "
            f"Invalid rows: {invalid_active_rows[['slug', 'name', 'is_active']].to_dict(orient='records')}"
        )

    return errors


def validate_seed_aliases(
    seed_aliases: pd.DataFrame,
    seed_topics: pd.DataFrame,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(
        check_required_columns(
            seed_aliases,
            SEED_ALIASES_REQUIRED_COLUMNS,
            "seed_aliases",
        )
    )

    if errors:
        return errors, warnings

    topic_slug_set = set(seed_topics["slug"].tolist())

    missing_topic_slug_rows = seed_aliases[
        ~seed_aliases["topic_slug"].isin(topic_slug_set)
    ]
    if not missing_topic_slug_rows.empty:
        errors.append(
            "[seed_aliases] topic_slug must exist in seed_topics.slug. "
            f"Invalid rows: {missing_topic_slug_rows[['topic_slug', 'alias_name']].to_dict(orient='records')}"
        )

    empty_alias_rows = seed_aliases[seed_aliases["alias_name"] == ""]
    if not empty_alias_rows.empty:
        errors.append(
            "[seed_aliases] alias_name must not be empty. "
            f"Invalid rows: {empty_alias_rows[['topic_slug', 'alias_name']].to_dict(orient='records')}"
        )

    valid_languages = {"ko", "en", "mixed", "unknown"}
    invalid_language_rows = seed_aliases[
        ~seed_aliases["language"].isin(valid_languages)
    ]
    if not invalid_language_rows.empty:
        errors.append(
            "[seed_aliases] Invalid language. "
            f"Allowed: {', '.join(sorted(valid_languages))}. "
            f"Invalid rows: {invalid_language_rows[['topic_slug', 'alias_name', 'language']].to_dict(orient='records')}"
        )

    valid_alias_types = {
        "synonym",
        "english",
        "abbreviation",
        "variant",
        "source_title",
        "manual",
    }
    invalid_alias_type_rows = seed_aliases[
        ~seed_aliases["alias_type"].isin(valid_alias_types)
    ]
    if not invalid_alias_type_rows.empty:
        errors.append(
            "[seed_aliases] Invalid alias_type. "
            f"Allowed: {', '.join(sorted(valid_alias_types))}. "
            f"Invalid rows: {invalid_alias_type_rows[['topic_slug', 'alias_name', 'alias_type']].to_dict(orient='records')}"
        )

    valid_match_policies = {"exact", "normalized_exact", "contains"}
    invalid_match_policy_rows = seed_aliases[
        ~seed_aliases["match_policy"].isin(valid_match_policies)
    ]
    if not invalid_match_policy_rows.empty:
        errors.append(
            "[seed_aliases] Invalid match_policy. "
            f"Allowed: {', '.join(sorted(valid_match_policies))}. "
            f"Invalid rows: {invalid_match_policy_rows[['topic_slug', 'alias_name', 'match_policy']].to_dict(orient='records')}"
        )

    valid_priorities = {"P0", "P1", "P2", "P3"}
    invalid_priority_rows = seed_aliases[
        ~seed_aliases["priority"].isin(valid_priorities)
    ]
    if not invalid_priority_rows.empty:
        errors.append(
            "[seed_aliases] Invalid priority. "
            f"Allowed: {', '.join(sorted(valid_priorities))}. "
            f"Invalid rows: {invalid_priority_rows[['topic_slug', 'alias_name', 'priority']].to_dict(orient='records')}"
        )

    duplicated_alias_rows = seed_aliases[
        seed_aliases.duplicated(subset=["topic_slug", "alias_name"], keep=False)
    ]
    if not duplicated_alias_rows.empty:
        errors.append(
            "[seed_aliases] Duplicate alias for same topic_slug. "
            f"Invalid rows: {duplicated_alias_rows[['topic_slug', 'alias_name']].to_dict(orient='records')}"
        )

    # 짧은 약어가 contains로 되어 있으면 오탐 위험이 크다.
    risky_short_contains = seed_aliases[
        (seed_aliases["alias_name"].str.len() <= 3)
        & (seed_aliases["match_policy"] == "contains")
    ]
    if not risky_short_contains.empty:
        warnings.append(
            "[seed_aliases] Short aliases with contains policy may cause false positives. "
            "Use exact or normalized_exact instead. "
            f"Risky rows: {risky_short_contains[['topic_slug', 'alias_name', 'match_policy']].to_dict(orient='records')}"
        )

    return errors, warnings


def validate_depth3_candidates(
    depth3_candidates: pd.DataFrame,
    seed_topics: pd.DataFrame,
) -> list[str]:
    errors: list[str] = []

    errors.extend(
        check_required_columns(
            depth3_candidates,
            DEPTH3_CANDIDATES_REQUIRED_COLUMNS,
            "depth3_candidates",
        )
    )

    if errors:
        return errors

    if depth3_candidates.empty:
        errors.append("[depth3_candidates] File is empty.")
        return errors

    seed_depth2_slugs = set(
        seed_topics[seed_topics["depth"] == "2"]["slug"].tolist()
    )

    invalid_parent_rows = depth3_candidates[
        ~depth3_candidates["suggested_parent_slug"].isin(seed_depth2_slugs)
    ]
    if not invalid_parent_rows.empty:
        errors.append(
            "[depth3_candidates] suggested_parent_slug must exist as depth=2 topic in seed_topics. "
            f"Invalid rows: {invalid_parent_rows[['candidate_name', 'suggested_parent_slug']].to_dict(orient='records')}"
        )

    invalid_depth_rows = depth3_candidates[
        depth3_candidates["suggested_depth"] != "3"
    ]
    if not invalid_depth_rows.empty:
        errors.append(
            "[depth3_candidates] suggested_depth must be 3. "
            f"Invalid rows: {invalid_depth_rows[['candidate_name', 'suggested_depth']].to_dict(orient='records')}"
        )

    valid_priorities = {"P0", "P1", "P2", "P3"}
    invalid_priority_rows = depth3_candidates[
        ~depth3_candidates["priority"].isin(valid_priorities)
    ]
    if not invalid_priority_rows.empty:
        errors.append(
            "[depth3_candidates] Invalid priority. "
            f"Allowed: {', '.join(sorted(valid_priorities))}. "
            f"Invalid rows: {invalid_priority_rows[['candidate_name', 'priority']].to_dict(orient='records')}"
        )

    valid_decision_hints = {
        "approved_candidate",
        "hold_candidate",
        "reject_candidate",
        "merge_candidate",
    }
    invalid_decision_hint_rows = depth3_candidates[
        ~depth3_candidates["decision_hint"].isin(valid_decision_hints)
    ]
    if not invalid_decision_hint_rows.empty:
        errors.append(
            "[depth3_candidates] Invalid decision_hint. "
            f"Allowed: {', '.join(sorted(valid_decision_hints))}. "
            f"Invalid rows: {invalid_decision_hint_rows[['candidate_name', 'decision_hint']].to_dict(orient='records')}"
        )

    duplicated_candidate_rows = depth3_candidates[
        depth3_candidates.duplicated(
            subset=["candidate_name", "suggested_parent_slug"],
            keep=False,
        )
    ]
    if not duplicated_candidate_rows.empty:
        errors.append(
            "[depth3_candidates] Duplicate candidate for same parent. "
            f"Invalid rows: {duplicated_candidate_rows[['candidate_name', 'suggested_parent_slug']].to_dict(orient='records')}"
        )

    return errors


def validate_curriculum_courses(curriculum_courses: pd.DataFrame) -> list[str]:
    errors: list[str] = []

    errors.extend(
        check_required_columns(
            curriculum_courses,
            CURRICULUM_REQUIRED_COLUMNS,
            "curriculum_courses",
        )
    )

    if errors:
        return errors

    if curriculum_courses.empty:
        errors.append("[curriculum_courses] File is empty.")
        return errors

    empty_course_name_rows = curriculum_courses[
        curriculum_courses["course_name"] == ""
    ]
    if not empty_course_name_rows.empty:
        errors.append(
            "[curriculum_courses] course_name should not be empty. "
            f"Empty count: {len(empty_course_name_rows)}"
        )

    return errors


def validate_learning_resources(learning_resources: pd.DataFrame) -> list[str]:
    errors: list[str] = []

    errors.extend(
        check_required_columns(
            learning_resources,
            LEARNING_RESOURCE_REQUIRED_COLUMNS,
            "learning_resources",
        )
    )

    if errors:
        return errors

    if learning_resources.empty:
        errors.append("[learning_resources] File is empty.")
        return errors

    empty_title_rows = learning_resources[learning_resources["title"] == ""]
    if not empty_title_rows.empty:
        errors.append(
            "[learning_resources] title should not be empty. "
            f"Empty count: {len(empty_title_rows)}"
        )

    empty_description_rows = learning_resources[
        learning_resources["description"] == ""
    ]
    if not empty_description_rows.empty:
        errors.append(
            "[learning_resources] description is empty. "
            f"Empty count: {len(empty_description_rows)}"
        )

    return errors


def summarize_dataframe(df: pd.DataFrame, name: str) -> dict[str, Any]:
    return {
        "name": name,
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": df.columns.tolist(),
    }


def build_validation_report(
    seed_topics: pd.DataFrame,
    seed_aliases: pd.DataFrame,
    depth3_candidates: pd.DataFrame,
    curriculum_courses: pd.DataFrame,
    learning_resources: pd.DataFrame,
    errors: list[str],
    warnings: list[str],
    input_paths: dict[str, Path],
) -> dict[str, Any]:
    return {
        "status": "success" if not errors else "failed",
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "input_paths": {
            name: str(path.resolve()) for name, path in input_paths.items()
        },
        "datasets": [
            summarize_dataframe(seed_topics, "seed_topics"),
            summarize_dataframe(seed_aliases, "seed_aliases"),
            summarize_dataframe(depth3_candidates, "depth3_candidates"),
            summarize_dataframe(curriculum_courses, "curriculum_courses"),
            summarize_dataframe(learning_resources, "learning_resources"),
        ],
        "seed_topic_summary": {
            "depth_counts": seed_topics["depth"].value_counts().to_dict()
            if "depth" in seed_topics.columns
            else {},
            "priority_counts": seed_topics["priority"].value_counts().to_dict()
            if "priority" in seed_topics.columns
            else {},
        },
        "alias_summary": {
            "match_policy_counts": seed_aliases["match_policy"].value_counts().to_dict()
            if "match_policy" in seed_aliases.columns
            else {},
            "language_counts": seed_aliases["language"].value_counts().to_dict()
            if "language" in seed_aliases.columns
            else {},
        },
        "depth3_candidate_summary": {
            "priority_counts": depth3_candidates["priority"].value_counts().to_dict()
            if "priority" in depth3_candidates.columns
            else {},
            "decision_hint_counts": depth3_candidates[
                "decision_hint"
            ].value_counts().to_dict()
            if "decision_hint" in depth3_candidates.columns
            else {},
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Step 1 - Load and validate topic pipeline CSV files."
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
        default=DEFAULT_CURRICULUM_PATH,
    )
    parser.add_argument(
        "--resources",
        type=Path,
        default=DEFAULT_LEARNING_RESOURCES_PATH,
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=PROCESSED_DIR / "validation_report.json",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    args.output_report.parent.mkdir(parents=True, exist_ok=True)

    seed_topics = read_csv_safely(
        args.seed_topics,
        empty_columns=SEED_TOPICS_REQUIRED_COLUMNS,
    )
    seed_aliases = read_csv_safely(
        args.seed_aliases,
        empty_columns=SEED_ALIASES_REQUIRED_COLUMNS,
    )
    depth3_candidates = read_csv_safely(
        args.depth3_candidates,
        empty_columns=DEPTH3_CANDIDATES_REQUIRED_COLUMNS,
    )
    curriculum_courses = read_csv_safely(
        args.curriculum,
        empty_columns=CURRICULUM_REQUIRED_COLUMNS,
    )
    learning_resources = read_csv_safely(
        args.resources,
        empty_columns=LEARNING_RESOURCE_REQUIRED_COLUMNS,
    )

    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(validate_seed_topics(seed_topics))
    seed_alias_errors, seed_alias_warnings = validate_seed_aliases(
        seed_aliases,
        seed_topics,
    )
    errors.extend(seed_alias_errors)
    warnings.extend(seed_alias_warnings)
    errors.extend(validate_depth3_candidates(depth3_candidates, seed_topics))
    errors.extend(validate_curriculum_courses(curriculum_courses))
    errors.extend(validate_learning_resources(learning_resources))

    report = build_validation_report(
        seed_topics=seed_topics,
        seed_aliases=seed_aliases,
        depth3_candidates=depth3_candidates,
        curriculum_courses=curriculum_courses,
        learning_resources=learning_resources,
        errors=errors,
        warnings=warnings,
        input_paths={
            "seed_topics": args.seed_topics,
            "seed_aliases": args.seed_aliases,
            "depth3_candidates": args.depth3_candidates,
            "curriculum_courses": args.curriculum,
            "learning_resources": args.resources,
        },
    )

    with args.output_report.open("w", encoding="utf-8-sig") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("=" * 80)
    print("Topic Pipeline Step 1 - Load & Validate")
    print("=" * 80)
    print(f"Status       : {report['status']}")
    print(f"Error count  : {report['error_count']}")
    print(f"Warning count: {report['warning_count']}")
    print(f"Report saved : {args.output_report}")

    print("\nDataset summary:")
    for dataset in report["datasets"]:
        print(
            f"- {dataset['name']}: "
            f"{dataset['row_count']} rows, {dataset['column_count']} columns"
        )

    if errors:
        print("\nValidation errors:")
        for idx, error in enumerate(errors, start=1):
            print(f"{idx}. {error}")
        raise SystemExit(1)

    if warnings:
        print("\nValidation warnings:")
        for idx, warning in enumerate(warnings, start=1):
            print(f"{idx}. {warning}")

    print("\nValidation passed.")


if __name__ == "__main__":
    main()
