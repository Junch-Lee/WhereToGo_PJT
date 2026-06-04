from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


SEED_TOPIC_REQUIRED_COLUMNS = [
    "slug",
    "name",
    "depth",
    "parent_slug",
    "topic_type",
    "priority",
    "is_active",
    "note",
]

SEED_ALIAS_REQUIRED_COLUMNS = [
    "topic_slug",
    "alias_name",
    "language",
    "alias_type",
    "match_policy",
    "priority",
    "note",
]

DEPTH3_REQUIRED_COLUMNS = [
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

FINAL_TOPIC_COLUMNS = [
    "topic_slug",
    "parent_topic_slug",
    "name",
    "depth",
    "topic_type",
    "is_learning_unit",
    "is_assessable",
    "description",
    "is_active",
    "source",
]

FINAL_ALIAS_COLUMNS = [
    "topic_lookup_key",
    "alias_name",
    "source",
    "language",
    "alias_type",
    "match_policy",
    "priority",
    "note",
]


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


def normalize_bool(value: str, default: str) -> str:
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return "true"
    if normalized in {"false", "0", "no", "n"}:
        return "false"
    return default


def normalize_depth(value: str, default: str) -> str:
    text = str(value).strip()
    if text == "":
        return default
    try:
        return str(int(float(text)))
    except ValueError:
        return text


def build_seed_topic_rows(seed_topics: pd.DataFrame, warnings: list[str]) -> pd.DataFrame:
    rows = []
    for idx, row in seed_topics.iterrows():
        depth = normalize_depth(row.get("depth", ""), "")
        if depth not in {"1", "2"}:
            warnings.append(f"seed topic row {idx}: depth '{row.get('depth', '')}' excluded; only depth 1~2 are used")
            continue

        default_type = "domain" if depth == "1" else "subject"
        rows.append(
            {
                "topic_slug": row.get("slug", ""),
                "parent_topic_slug": "" if depth == "1" else row.get("parent_slug", ""),
                "name": row.get("name", ""),
                "depth": depth,
                "topic_type": row.get("topic_type", "") or default_type,
                "is_learning_unit": "false",
                "is_assessable": "false" if depth == "1" else "true",
                "description": row.get("note", ""),
                "is_active": normalize_bool(row.get("is_active", ""), "true"),
                "source": "seed",
            }
        )
    return pd.DataFrame(rows, columns=FINAL_TOPIC_COLUMNS)


def build_depth3_topic_rows(depth3_topics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in depth3_topics.iterrows():
        description = row.get("description", "") or row.get("reviewer_note", "")
        rows.append(
            {
                "topic_slug": row.get("topic_slug", ""),
                "parent_topic_slug": row.get("parent_topic_slug", ""),
                "name": row.get("name", ""),
                "depth": normalize_depth(row.get("depth", ""), "3"),
                "topic_type": row.get("topic_type", "") or "concept",
                "is_learning_unit": "true",
                "is_assessable": "true",
                "description": description,
                "is_active": normalize_bool(row.get("is_active", ""), "true"),
                "source": "review",
            }
        )
    return pd.DataFrame(rows, columns=FINAL_TOPIC_COLUMNS)


def validate_and_dedupe_topics(topics: pd.DataFrame, warnings: list[str]) -> tuple[pd.DataFrame, int, int]:
    excluded_count = 0
    invalid_parent_count = 0
    valid_rows = []
    seen_slugs = set()

    topics_with_priority = topics.copy()
    topics_with_priority["_source_priority"] = topics_with_priority["source"].map({"seed": 0, "review": 1}).fillna(2)
    sorted_topics = topics_with_priority.sort_values(
        by=["topic_slug", "_source_priority"],
        ascending=[True, True],
        kind="mergesort",
    )

    for idx, row in sorted_topics.iterrows():
        topic_slug = row.get("topic_slug", "")
        name = row.get("name", "")
        source = row.get("source", "")

        if topic_slug == "":
            excluded_count += 1
            warnings.append(f"topic row {idx}: empty topic_slug excluded")
            continue
        if name == "":
            excluded_count += 1
            warnings.append(f"topic row {idx}: empty name excluded for topic_slug '{topic_slug}'")
            continue
        if topic_slug in seen_slugs:
            excluded_count += 1
            warnings.append(f"topic row {idx}: duplicate topic_slug '{topic_slug}' excluded; seed rows are preferred")
            continue

        seen_slugs.add(topic_slug)
        row_dict = row.to_dict()
        row_dict.pop("_source_priority", None)
        valid_rows.append(row_dict)

    final_topics = pd.DataFrame(valid_rows, columns=FINAL_TOPIC_COLUMNS)
    final_slugs = set(final_topics["topic_slug"].tolist()) if not final_topics.empty else set()

    for idx, row in final_topics.iterrows():
        depth = normalize_depth(row.get("depth", ""), "")
        parent_slug = row.get("parent_topic_slug", "")
        if depth in {"2", "3"} and parent_slug not in final_slugs:
            invalid_parent_count += 1
            warnings.append(
                f"topic row {idx}: parent_topic_slug '{parent_slug}' not found for topic_slug '{row.get('topic_slug', '')}'"
            )

    return final_topics.reset_index(drop=True), invalid_parent_count, excluded_count


def build_alias_rows(seed_aliases: pd.DataFrame, final_topics: pd.DataFrame, warnings: list[str]) -> tuple[pd.DataFrame, int]:
    final_slugs = set(final_topics["topic_slug"].tolist()) if not final_topics.empty else set()
    rows = []
    seen_aliases = set()
    excluded_count = 0

    for idx, row in seed_aliases.iterrows():
        topic_lookup_key = row.get("topic_slug", "")
        alias_name = row.get("alias_name", "")

        if alias_name == "":
            excluded_count += 1
            warnings.append(f"alias row {idx}: empty alias_name excluded for topic_lookup_key '{topic_lookup_key}'")
            continue
        if topic_lookup_key not in final_slugs:
            excluded_count += 1
            warnings.append(f"alias row {idx}: topic_lookup_key '{topic_lookup_key}' not found in final topics")
            continue

        alias_key = (topic_lookup_key, alias_name)
        if alias_key in seen_aliases:
            excluded_count += 1
            warnings.append(f"alias row {idx}: duplicate alias '{alias_name}' for topic_lookup_key '{topic_lookup_key}' excluded")
            continue

        seen_aliases.add(alias_key)
        rows.append(
            {
                "topic_lookup_key": topic_lookup_key,
                "alias_name": alias_name,
                "source": "seed",
                "language": row.get("language", ""),
                "alias_type": row.get("alias_type", ""),
                "match_policy": row.get("match_policy", ""),
                "priority": row.get("priority", ""),
                "note": row.get("note", ""),
            }
        )

    aliases = pd.DataFrame(rows, columns=FINAL_ALIAS_COLUMNS)
    return aliases, excluded_count


def value_counts_as_dict(df: pd.DataFrame, column: str) -> dict:
    if df.empty:
        return {}
    counts = df[column].value_counts().to_dict()
    return {str(key): int(value) for key, value in counts.items()}


def build_report(
    seed_topics: pd.DataFrame,
    seed_aliases: pd.DataFrame,
    depth3_topics: pd.DataFrame,
    final_topics: pd.DataFrame,
    final_aliases: pd.DataFrame,
    invalid_parent_count: int,
    excluded_topic_count: int,
    excluded_alias_count: int,
    warnings: list[str],
) -> dict:
    depth_counts = value_counts_as_dict(final_topics, "depth")
    for depth in ["1", "2", "3"]:
        depth_counts.setdefault(depth, 0)

    return {
        "status": "success",
        "inputs": {
            "seed_topics": int(len(seed_topics)),
            "seed_aliases": int(len(seed_aliases)),
            "approved_depth3_topics": int(len(depth3_topics)),
        },
        "outputs": {
            "final_topics": int(len(final_topics)),
            "final_topic_aliases": int(len(final_aliases)),
        },
        "summary": {
            "topic_depth_counts": depth_counts,
            "topic_type_counts": value_counts_as_dict(final_topics, "topic_type"),
            "topic_source_counts": value_counts_as_dict(final_topics, "source"),
            "alias_source_counts": value_counts_as_dict(final_aliases, "source"),
            "invalid_parent_topic_count": int(invalid_parent_count),
            "excluded_topic_count": int(excluded_topic_count),
            "excluded_alias_count": int(excluded_alias_count),
        },
        "warnings": warnings,
    }


def write_outputs(output_dir: Path, final_topics: pd.DataFrame, final_aliases: pd.DataFrame, report: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    final_topics.to_csv(output_dir / "final_topics_import.csv", index=False, encoding="utf-8-sig")
    final_aliases.to_csv(output_dir / "final_topic_aliases_import.csv", index=False, encoding="utf-8-sig")

    with (output_dir / "final_topics_aliases_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def print_summary(report: dict, output_dir: Path) -> None:
    print("Status:", report["status"])
    print("seed topic input rows:", report["inputs"]["seed_topics"])
    print("approved depth3 input rows:", report["inputs"]["approved_depth3_topics"])
    print("final topic rows:", report["outputs"]["final_topics"])
    print("final alias rows:", report["outputs"]["final_topic_aliases"])
    print("depth topic counts:")
    for depth, count in report["summary"]["topic_depth_counts"].items():
        print(f"- {depth}: {count}")
    print("invalid parent count:", report["summary"]["invalid_parent_topic_count"])
    print("excluded topic count:", report["summary"]["excluded_topic_count"])
    print("excluded alias count:", report["summary"]["excluded_alias_count"])
    print("output directory:", output_dir)
    print("warnings count:", len(report["warnings"]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Step 08 - Build final topic and alias import CSVs with natural lookup keys."
    )
    parser.add_argument(
        "--seed-topics",
        type=Path,
        default=Path("curriculum-data/seed/seed_topics_v0.2.csv"),
        help="Path to seed topics CSV.",
    )
    parser.add_argument(
        "--seed-aliases",
        type=Path,
        default=Path("curriculum-data/seed/seed_aliases_v0.1.csv"),
        help="Path to seed aliases CSV.",
    )
    parser.add_argument(
        "--approved-depth3",
        type=Path,
        default=Path("scripts/topic_pipeline/data/final/final_topics_depth3_import.csv"),
        help="Path to Step 07 approved depth3 final topics CSV.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("scripts/topic_pipeline/data/final"),
        help="Directory for final topic and alias import CSV outputs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    warnings = []

    seed_topics = read_csv_safely(args.seed_topics)
    seed_aliases = read_csv_safely(args.seed_aliases)
    depth3_topics = read_csv_safely(args.approved_depth3)

    validate_required_columns(seed_topics, SEED_TOPIC_REQUIRED_COLUMNS, "seed_topics_v0.2.csv")
    validate_required_columns(seed_aliases, SEED_ALIAS_REQUIRED_COLUMNS, "seed_aliases_v0.1.csv")
    validate_required_columns(depth3_topics, DEPTH3_REQUIRED_COLUMNS, "final_topics_depth3_import.csv")

    seed_topic_rows = build_seed_topic_rows(seed_topics, warnings)
    depth3_topic_rows = build_depth3_topic_rows(depth3_topics)
    combined_topics = pd.concat([seed_topic_rows, depth3_topic_rows], ignore_index=True)
    final_topics, invalid_parent_count, excluded_topic_count = validate_and_dedupe_topics(combined_topics, warnings)

    final_aliases, excluded_alias_count = build_alias_rows(seed_aliases, final_topics, warnings)
    report = build_report(
        seed_topics,
        seed_aliases,
        depth3_topics,
        final_topics,
        final_aliases,
        invalid_parent_count,
        excluded_topic_count,
        excluded_alias_count,
        warnings,
    )

    write_outputs(args.output_dir, final_topics, final_aliases, report)
    print_summary(report, args.output_dir)


if __name__ == "__main__":
    main()
