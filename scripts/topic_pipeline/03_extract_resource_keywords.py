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

<<<<<<< HEAD
# 쉼표로 나뉜 뒤에도 한 항목 안에 여러 개념이 붙어 있는 경우가 있다.
# 이 패턴은 "및", "과", "와" 같은 연결어를 기준으로 복합 키워드를 추가 분리한다.
CONNECTOR_KEYWORD_PATTERN = re.compile(
    r"\s+(?:및|그리고|또는|또|혹은)\s+|(?<=[가-힣A-Za-z0-9\)])(?:과|와)\s+"
)

# "에 대한 이해", "역량 습득"처럼 강의 목표 문장에 붙는 끝 표현은
# 키워드 자체가 아니므로 분리 후 제거해 짧고 재사용 가능한 키워드로 만든다.
TRAILING_LEARNING_OUTCOME_PATTERN = re.compile(
    r"\s*(?:에\s*대한\s*)?"
    r"(?:(?:활용|문제\s*해결)\s*)?"
    r"(?:능력|역량|기술|전략)?\s*"
    r"(?:이해|습득|배양|경험|탐색|학습)\s*$"
)

STANDALONE_LEARNING_OUTCOME_WORDS = {
    "이해",
    "습득",
    "배양",
    "경험",
    "탐색",
    "학습",
    "활용",
    "구현",
}

=======
>>>>>>> origin/develop
INVISIBLE_CHARS_PATTERN = re.compile(
    r"[\u200b\u200c\u200d\ufeff\u00a0]"
)

MULTI_SPACE_PATTERN = re.compile(r"\s+")

<<<<<<< HEAD
''' 
1. 키워드 추출을 위한 보조 함수 정의 구간
- csv 로드 함수
- 유니코드 정규화
- 안전 문자 및 공백 제거 
- 불규칙적 공백 정규화 

'''
=======
>>>>>>> origin/develop

def read_csv_safely(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

<<<<<<< HEAD
    # 한글 데이터가 CP949로 재해석되며 손실되는 일을 막기 위해 UTF-8 계열만 허용한다.
    # utf-8-sig는 BOM이 있는 CSV와 없는 CSV를 모두 안전하게 읽을 수 있다.
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
=======
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="cp949")
>>>>>>> origin/develop

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


<<<<<<< HEAD
def remove_trailing_learning_outcome(text: str) -> str:
    """
    키워드 뒤에 붙은 학습성과 표현을 제거한다.

    예:
    '윤리적 쟁점에 대한 이해' -> '윤리적 쟁점'
    '리스크 관리 역량 습득' -> '리스크 관리'
    """
    text = clean_text(text)
    if not text:
        return ""

    cleaned = TRAILING_LEARNING_OUTCOME_PATTERN.sub("", text).strip()
    return cleaned or text


def split_keyword_by_connectors(keyword: str) -> list[str]:
    """
    쉼표로 분리된 키워드 안에 남아 있는 연결어를 기준으로 한 번 더 분리한다.

    예:
    'AI 시스템 보안 및 리스크 관리 역량 습득'
    -> ['AI 시스템 보안', '리스크 관리']
    """
    keyword = clean_text(keyword)
    if not keyword:
        return []

    parts = CONNECTOR_KEYWORD_PATTERN.split(keyword)
    refined_items: list[str] = []

    for part in parts:
        item = remove_trailing_learning_outcome(part)

        # "및 활용", "및 구현 경험"처럼 연결어 뒤에 행위어만 남은 경우는
        # 독립 키워드로 쓰기 어렵기 때문에 제외한다.
        if normalize_for_match(item) in STANDALONE_LEARNING_OUTCOME_WORDS:
            continue

        if item:
            refined_items.append(item)

    return refined_items


=======
>>>>>>> origin/develop
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
<<<<<<< HEAD
        connector_split_items = split_keyword_by_connectors(part)

        for item in connector_split_items:
            if not item:
                continue

            # 연결어와 학습성과 표현을 제거한 뒤 동일 키워드가 반복될 수 있으므로
            # 비교용 정규화 문자열로 중복을 제거해 exploded 결과의 노이즈를 줄인다.
            normalized_key = normalize_for_match(item)

            if normalized_key in seen:
                continue

            seen.add(normalized_key)
            cleaned_items.append(item)
=======
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
>>>>>>> origin/develop

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
<<<<<<< HEAD
        default=Path("scripts/topic_pipeline/data/processed/learning_resources_normalized.csv"),
    )

    # 1. extracted : 키워드 존재 여부, 본문, 키워드 문자열, 키워드 리스트 JSON, 개수 컬럼 존재
    parser.add_argument(
        "--output-resources",
        type=Path,
        default=Path("scripts/topic_pipeline/data/keywords/learning_resources_keywords_extracted.csv"),
    )

    # 2. exploded : 키워드를 한 row씩 펼쳐둔 파일
    parser.add_argument(
        "--output-keywords",
        type=Path,
        default=Path("scripts/topic_pipeline/data/keywords/learning_resource_keywords_exploded.csv"),
    )

    # 3. 키워드 추출 report
    parser.add_argument(
        "--output-report",
        type=Path,
        default=Path("scripts/topic_pipeline/data/keywords/keyword_extraction_report.json"),
=======
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
>>>>>>> origin/develop
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
