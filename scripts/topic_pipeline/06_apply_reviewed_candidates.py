from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd


ALLOWED_DECISIONS = {"approved", "merged", "rejected", "hold", "pending"}
DECISION_ORDER = ["approved", "merged", "rejected", "hold", "pending"]

REQUIRED_COLUMNS = [
    "candidate_name",
    "suggested_parent_slug",
    "suggested_depth",
    "occurrence_count",
    "max_relevance_score",
    "avg_relevance_score",
    "decision",
    "merge_target_topic_slug",
    "reviewer_note",
]

APPROVED_COLUMNS = [
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

# Manual mapping for reviewed depth3 candidate names. Keep this in-code so Step 06
# does not depend on a separate slug mapping CSV.
MANUAL_SLUG_MAP = {
    "변수": "variable",
    "자료형": "data-type",
    "조건문": "conditional-statement",
    "반복문": "loop",
    "함수": "function",
    "표현식": "expression",
    "배열": "array",
    "리스트": "list",
    "스택": "stack",
    "큐": "queue",
    "트리": "tree",
    "그래프 자료구조": "graph-data-structure",
    "해시": "hash",
    "정렬": "sorting",
    "탐색": "searching",
    "재귀": "recursion",
    "동적 계획법": "dynamic-programming",
    "그리디 알고리즘": "greedy-algorithm",
    "BFS": "bfs",
    "DFS": "dfs",
    "프로토콜": "protocol",
    "OSI 7계층": "osi-7-layer",
    "TCP/IP": "tcp-ip",
    "HTTP": "http",
    "DNS": "dns",
    "라우팅": "routing",
    "인터넷": "internet",
    "쿼리": "query",
    "SELECT": "select",
    "INSERT": "insert",
    "UPDATE": "update",
    "DELETE": "delete",
    "JOIN": "join",
    "GROUP BY": "group-by",
    "인덱스": "index",
    "ERD": "erd",
    "벡터": "vector",
    "행렬": "matrix",
    "벡터공간": "vector-space",
    "선형변환": "linear-transformation",
    "역행렬": "inverse-matrix",
    "대각화": "diagonalization",
    "고윳값과 고유벡터": "eigenvalue-eigenvector",
    "특잇값 분해": "singular-value-decomposition",
    "표본추출": "sampling",
    "확률분포": "probability-distribution",
    "기댓값과 분산": "expectation-variance",
    "가설검정": "hypothesis-testing",
    "경사하강법": "gradient-descent",
    "지도학습": "supervised-learning",
    "비지도학습": "unsupervised-learning",
    "분류": "classification",
    "회귀": "regression",
    "클러스터링": "clustering",
    "과적합": "overfitting",
    "교차 검증": "cross-validation",
    "신경망": "neural-network",
    "역전파": "backpropagation",
    "CNN": "cnn",
    "RNN": "rnn",
    "Transformer": "transformer",
    "임베딩": "embedding",
    "벡터 검색": "vector-search",
    "벡터 데이터베이스": "vector-database",
    "프롬프트 엔지니어링": "prompt-engineering",
    "LLM": "llm",
    "RAG": "rag",
    "공간복잡도": "space-complexity",
    "시간복잡도": "time-complexity",
}


def read_csv_safely(path: Path) -> pd.DataFrame:
    """Read a review CSV as strings with Korean-friendly encoding fallback."""
    if not path.exists():
        raise FileNotFoundError(f"Input review CSV not found: {path}")

    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="cp949")

    df.columns = [str(col).strip() for col in df.columns]
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    return df


def validate_required_columns(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))


def normalize_decisions(df: pd.DataFrame):
    """Normalize decision values and turn unknown values into pending."""
    normalized_df = df.copy()
    warnings = []

    normalized_df["decision"] = normalized_df["decision"].str.lower().str.strip()
    invalid_mask = ~normalized_df["decision"].isin(ALLOWED_DECISIONS)

    if invalid_mask.any():
        invalid_rows = normalized_df[invalid_mask]
        for idx, row in invalid_rows.iterrows():
            raw_decision = row.get("decision", "")
            candidate_name = row.get("candidate_name", "")
            warnings.append(
                f"row {idx}: invalid decision '{raw_decision}' for '{candidate_name}', treated as pending"
            )
        normalized_df.loc[invalid_mask, "decision"] = "pending"

    return normalized_df, warnings


def to_int(value: str, default: int = 0) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def make_priority(occurrence_count: str) -> str:
    count = to_int(occurrence_count, default=0)
    if count >= 10:
        return "P0"
    return "P1"


def fallback_slug(candidate_name: str, row_index: int) -> str:
    slug = candidate_name.lower().strip()
    slug = slug.replace("/", "-")
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")

    if not slug:
        return f"topic-{row_index + 1}"
    return slug


def make_unique_slug(base_slug: str, parent_slug: str, used_slugs):
    slug = base_slug
    if slug in used_slugs and parent_slug:
        slug = f"{parent_slug}-{base_slug}"

    if slug not in used_slugs:
        used_slugs.add(slug)
        return slug

    suffix = 2
    while f"{slug}-{suffix}" in used_slugs:
        suffix += 1

    unique_slug = f"{slug}-{suffix}"
    used_slugs.add(unique_slug)
    return unique_slug


def build_approved_topics(approved_df: pd.DataFrame) -> pd.DataFrame:
    """Convert approved candidate rows into depth3 topic rows."""
    if approved_df.empty:
        return pd.DataFrame(columns=APPROVED_COLUMNS)

    rows = []
    used_slugs = set()

    for row_idx, (idx, row) in enumerate(approved_df.iterrows()):
        candidate_name = row.get("candidate_name", "")
        parent_slug = row.get("suggested_parent_slug", "")
        base_slug = MANUAL_SLUG_MAP.get(candidate_name, "")
        if not base_slug:
            base_slug = fallback_slug(candidate_name, int(row_idx))
        slug = make_unique_slug(base_slug, parent_slug, used_slugs)
        depth = row.get("suggested_depth", "") or "3"

        rows.append(
            {
                "slug": slug,
                "name": candidate_name,
                "depth": depth,
                "parent_slug": parent_slug,
                "topic_type": "concept",
                "priority": make_priority(row.get("occurrence_count", "")),
                "is_active": "true",
                "source_candidate_name": candidate_name,
                "occurrence_count": row.get("occurrence_count", ""),
                "max_relevance_score": row.get("max_relevance_score", ""),
                "avg_relevance_score": row.get("avg_relevance_score", ""),
                "reviewer_note": row.get("reviewer_note", ""),
            }
        )

    return pd.DataFrame(rows, columns=APPROVED_COLUMNS)


def split_by_decision(df: pd.DataFrame):
    return {
        decision: df[df["decision"] == decision].copy()
        for decision in DECISION_ORDER
    }


def collect_merge_warnings(merged_df: pd.DataFrame):
    warnings = []
    if merged_df.empty:
        return warnings

    missing_target_df = merged_df[merged_df["merge_target_topic_slug"].str.strip() == ""]
    for idx, row in missing_target_df.iterrows():
        warnings.append(
            f"row {idx}: merged candidate '{row.get('candidate_name', '')}' has empty merge_target_topic_slug"
        )

    return warnings


def write_csv_outputs(output_dir: Path, approved_topics: pd.DataFrame, decision_frames):
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "approved_depth3_topics": output_dir / "approved_depth3_topics.csv",
        "merged_candidates": output_dir / "merged_topic_candidates.csv",
        "rejected_candidates": output_dir / "rejected_topic_candidates.csv",
        "hold_candidates": output_dir / "hold_topic_candidates.csv",
        "pending_candidates": output_dir / "pending_topic_candidates.csv",
    }

    approved_topics.to_csv(paths["approved_depth3_topics"], index=False, encoding="utf-8-sig")
    decision_frames["merged"].to_csv(paths["merged_candidates"], index=False, encoding="utf-8-sig")
    decision_frames["rejected"].to_csv(paths["rejected_candidates"], index=False, encoding="utf-8-sig")
    decision_frames["hold"].to_csv(paths["hold_candidates"], index=False, encoding="utf-8-sig")
    decision_frames["pending"].to_csv(paths["pending_candidates"], index=False, encoding="utf-8-sig")

    return paths


def build_report(input_rows: int, decision_frames, approved_topics: pd.DataFrame, warnings):
    return {
        "status": "success",
        "input_rows": int(input_rows),
        "decision_counts": {
            decision: int(len(decision_frames[decision]))
            for decision in DECISION_ORDER
        },
        "outputs": {
            "approved_depth3_topics": int(len(approved_topics)),
            "merged_candidates": int(len(decision_frames["merged"])),
            "rejected_candidates": int(len(decision_frames["rejected"])),
            "hold_candidates": int(len(decision_frames["hold"])),
            "pending_candidates": int(len(decision_frames["pending"])),
        },
        "warnings": warnings,
    }


def write_report(report, output_dir: Path) -> Path:
    report_path = output_dir / "topic_review_apply_report.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report_path


def print_summary(report, output_dir: Path, approved_topics: pd.DataFrame) -> None:
    print("Status:", report["status"])
    print("input rows:", report["input_rows"])
    print("decision counts:")
    for decision in DECISION_ORDER:
        print(f"- {decision}: {report['decision_counts'][decision]}")
    print("approved depth3 topics count:", report["outputs"]["approved_depth3_topics"])
    print("merged candidates count:", report["outputs"]["merged_candidates"])
    print("rejected candidates count:", report["outputs"]["rejected_candidates"])
    print("hold candidates count:", report["outputs"]["hold_candidates"])
    print("pending candidates count:", report["outputs"]["pending_candidates"])
    print("output directory:", output_dir)
    print("warnings count:", len(report["warnings"]))
    print("approved top 10 topic names:")
    if approved_topics.empty:
        print("- none")
        return

    for name in approved_topics["name"].head(10):
        print(f"- {name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Step 06 - Apply reviewed topic candidate decisions."
    )
    parser.add_argument(
        "--input-review",
        type=Path,
        default=Path("scripts/topic_pipeline/data/review/topic_candidates_review_auto_labeled.csv"),
        help="Path to the reviewed topic candidate CSV.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("scripts/topic_pipeline/data/final"),
        help="Directory for final approved/rejected/hold/pending/merged outputs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    review_df = read_csv_safely(args.input_review)
    validate_required_columns(review_df)

    review_df, warnings = normalize_decisions(review_df)
    decision_frames = split_by_decision(review_df)
    warnings.extend(collect_merge_warnings(decision_frames["merged"]))

    approved_topics = build_approved_topics(decision_frames["approved"])
    write_csv_outputs(args.output_dir, approved_topics, decision_frames)
    report = build_report(
        input_rows=len(review_df),
        decision_frames=decision_frames,
        approved_topics=approved_topics,
        warnings=warnings,
    )
    write_report(report, args.output_dir)
    print_summary(report, args.output_dir, approved_topics)


if __name__ == "__main__":
    main()
