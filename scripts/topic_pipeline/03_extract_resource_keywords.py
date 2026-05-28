from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd


KEYWORD_MARKER_PATTERN = re.compile(
    r"(키워드|keyword|keywords)\s*[:：]",
    re.IGNORECASE,
)

SPLIT_KEYWORD_PATTERN = re.compile(r"[,;；、\n]+")

INVISIBLE_CHARS_PATTERN = re.compile(
    r"[\u200b\u200c\u200d\ufeff\u00a0]"
)

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


def normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def remove_invisible_chars(text: str) -> str:
    return INVISIBLE_CHARS_PATTERN.sub(" ", text)


def normalize_spacing(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = text.replace("\t", " ")
    text = MULTI_SPACE_PATTERN.sub(" ", text)
    return text.strip()


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value)
    text = normalize_unicode(text)
    text = remove_invisible_chars(text)
    text = normalize_spacing(text)

    return text


def normalize_for_match(value: Any) -> str:
    text = clean_text(value)
    text = text.lower()
    text = normalize_spacing(text)
    return text


def split_description_keyword_section(description: str) -> dict[str, Any]:
    """
    description에서 '키워드:' 또는 'Keywords:' 영역을 분리한다.

    반환:
    {
      "has_keyword_section": bool,
      "body": str,
      "keywords_raw": str,
      "keyword_items": list[str]
    }
    """
    description = clean_text(description)

    if not description:
        return {
            "has_keyword_section": False,
            "body": "",
            "keywords_raw": "",
            "keyword_items": [],
        }

    match = KEYWORD_MARKER_PATTERN.search(description)

    if not match:
        return {
            "has_keyword_section": False,
            "body": description,
            "keywords_raw": "",
            "keyword_items": [],
        }

    body = description[: match.start()].strip()
    keywords_raw = description[match.end() :].strip()

    keyword_items = split_keyword_items(keywords_raw)

    return {
        "has_keyword_section": True,
        "body": body,
        "keywords_raw": keywords_raw,
        "keyword_items": keyword_items,
    }


def split_keyword_items(keywords_raw: str) -> list[str]:
    """
    키워드 원문을 개별 키워드로 분리한다.

    예:
    '파이썬, 조건문, 반복문, 함수(Function)'
    -> ['파이썬', '조건문', '반복문', '함수(Function)']
    """
    keywords_raw = clean_text(keywords_raw)

    if not keywords_raw:
        return []

    parts = SPLIT_KEYWORD_PATTERN.split(keywords_raw)

    cleaned_items: list[str] = []
    seen: set[str] = set()

    for part in parts:
        item = clean_text(part)

        if not item:
            continue

        # 너무 긴 문장은 키워드가 아니라 설명일 가능성이 높음.
        # 단, 지금은 제거하지 않고 보수적으로 유지한다.
        normalized_key = normalize_for_match(item)

        if normalized_key in seen:
            continue

        seen.add(normalized_key)
        cleaned_items.append(item)

    return cleaned_items


def extract_keywords_from_resources(resources_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    result_df = resources_df.copy()

    if "description_clean" not in result_df.columns:
        raise ValueError(
            "description_clean column not found. "
            "Run step02_normalize_text.py first."
        )

    extracted_rows: list[dict[str, Any]] = []
    exploded_rows: list[dict[str, Any]] = []

    for idx, row in result_df.iterrows():
        description = row.get("description_clean", "")
        parsed = split_description_keyword_section(description)

        keyword_items = parsed["keyword_items"]

        extracted_rows.append(
            {
                "has_keyword_section": str(parsed["has_keyword_section"]).lower(),
                "description_body_clean": parsed["body"],
                "description_body_match": normalize_for_match(parsed["body"]),
                "description_keywords_raw": parsed["keywords_raw"],
                "description_keywords_match": normalize_for_match(parsed["keywords_raw"]),
                "description_keyword_items_json": json.dumps(
                    keyword_items,
                    ensure_ascii=False,
                ),
                "description_keyword_count": len(keyword_items),
            }
        )

        for keyword_order, keyword in enumerate(keyword_items, start=1):
            exploded_rows.append(
                {
                    "resource_row_index": idx,
                    "source_type": row.get("source_type", ""),
                    "external_id": row.get("external_id", ""),
                    "title": row.get("title", ""),
                    "title_clean": row.get("title_clean", ""),
                    "keyword_order": keyword_order,
                    "keyword": keyword,
                    "keyword_match": normalize_for_match(keyword),
                }
            )

    extracted_df = pd.DataFrame(extracted_rows)
    result_df = pd.concat([result_df, extracted_df], axis=1)

    exploded_df = pd.DataFrame(
        exploded_rows,
        columns=[
            "resource_row_index",
            "source_type",
            "external_id",
            "title",
            "title_clean",
            "keyword_order",
            "keyword",
            "keyword_match",
        ],
    )

    report = build_report(result_df, exploded_df)

    return result_df, exploded_df, report


def build_report(result_df: pd.DataFrame, exploded_df: pd.DataFrame) -> dict[str, Any]:
    total_rows = len(result_df)

    has_keyword_count = int(
        (result_df["has_keyword_section"] == "true").sum()
    )

    no_keyword_count = total_rows - has_keyword_count

    keyword_counts = (
        result_df["description_keyword_count"]
        .astype(int)
        .describe()
        .to_dict()
        if total_rows > 0
        else {}
    )

    top_keywords = (
        exploded_df["keyword_match"]
        .value_counts()
        .head(30)
        .to_dict()
        if not exploded_df.empty
        else {}
    )

    return {
        "status": "success",
        "total_resource_rows": int(total_rows),
        "has_keyword_section_count": has_keyword_count,
        "no_keyword_section_count": int(no_keyword_count),
        "total_exploded_keywords": int(len(exploded_df)),
        "keyword_count_stats": keyword_counts,
        "top_keywords": top_keywords,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Step 3 - Extract keyword section from learning resource descriptions."
    )

    parser.add_argument(
        "--input-resources",
        type=Path,
        default=Path("data/processed/learning_resources_normalized.csv"),
    )
    parser.add_argument(
        "--output-resources",
        type=Path,
        default=Path("data/processed/learning_resources_keywords_extracted.csv"),
    )
    parser.add_argument(
        "--output-keywords",
        type=Path,
        default=Path("data/processed/learning_resource_keywords_exploded.csv"),
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=Path("data/processed/keyword_extraction_report.json"),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    args.output_resources.parent.mkdir(parents=True, exist_ok=True)
    args.output_keywords.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.parent.mkdir(parents=True, exist_ok=True)

    resources_df = read_csv_safely(args.input_resources)

    result_df, exploded_df, report = extract_keywords_from_resources(resources_df)

    result_df.to_csv(
        args.output_resources,
        index=False,
        encoding="utf-8-sig",
    )

    exploded_df.to_csv(
        args.output_keywords,
        index=False,
        encoding="utf-8-sig",
    )

    with args.output_report.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("=" * 80)
    print("Topic Pipeline Step 3 - Extract Resource Keywords")
    print("=" * 80)
    print("Status: success")
    print(f"Input resources     : {args.input_resources}")
    print(f"Output resources    : {args.output_resources}")
    print(f"Output keywords     : {args.output_keywords}")
    print(f"Report output       : {args.output_report}")

    print("\nSummary:")
    print(f"- total_resource_rows       : {report['total_resource_rows']}")
    print(f"- has_keyword_section_count : {report['has_keyword_section_count']}")
    print(f"- no_keyword_section_count  : {report['no_keyword_section_count']}")
    print(f"- total_exploded_keywords   : {report['total_exploded_keywords']}")

    print("\nTop keywords:")
    for keyword, count in list(report["top_keywords"].items())[:15]:
        print(f"- {keyword}: {count}")


if __name__ == "__main__":
    main()
