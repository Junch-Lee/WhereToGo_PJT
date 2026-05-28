from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd


CURRICULUM_TEXT_FIELDS = [
    "course_name",
    "learning_objective",
    "prerequisite_material",
    "main_textbook",
    "reference_material",
]

RESOURCE_TEXT_FIELDS = [
    "title",
    "description",
]


NULL_LIKE_VALUES = {
    "",
    "없음",
    "없슴",
    "해당없음",
    "해당 없음",
    "무",
    "n/a",
    "na",
    "none",
    "null",
    "없다",
    "추후 공고",
    "추후공지",
    "추후 공지",
    "-",
    "--",
}


INVISIBLE_CHARS_PATTERN = re.compile(
    r"[\u200b\u200c\u200d\ufeff\u00a0]"
)

MULTI_SPACE_PATTERN = re.compile(r"\s+")
MULTI_SEPARATOR_PATTERN = re.compile(r"([,;:/|])\s*")


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


def clean_basic_text(value: Any) -> str:
    '''
    앞서 정의해둔 함수를 기반으로 텍스트 정규화를 실시하는 함수
    1. 유니코드 정규화
    2. 인코딩 과정에서 소실된 문자인 공백 제거
    3. 불필요/과도한 공백 제거
    '''
    if value is None:
        return ""

    text = str(value)
    text = normalize_unicode(text)
    text = remove_invisible_chars(text)
    text = normalize_spacing(text)

    if text.strip().lower() in NULL_LIKE_VALUES:
        return ""

    return text


def normalize_for_match(value: Any) -> str:
    """
    매칭용 텍스트를 만든다.

    원칙:
    - 원본 의미를 크게 훼손하지 않는다.
    - 영문은 소문자화한다.
    - 공백은 하나로 통일한다.
    - 특수문자를 무리하게 제거하지 않는다.
      예: C언어, REST API, CI/CD, TCP/IP 보존 필요
    """
    text = clean_basic_text(value)
    text = text.lower()
    text = normalize_spacing(text)

    return text


def clean_textbook_noise(value: Any) -> str:
    """
    교재 필드는 저자명, 출판사, 연도 등이 많이 섞여 있다.
    이 단계에서는 과하게 제거하지 않고,
    명백한 prefix와 불필요한 반복 표현만 완화한다.
    """
    text = clean_basic_text(value)

    if not text:
        return ""

    noise_prefixes = [
        "주교재:",
        "주교재 :",
        "교재:",
        "교재 :",
        "부교재:",
        "부교재 :",
        "참고문헌:",
        "참고문헌 :",
        "참고자료:",
        "참고자료 :",
        "[교재]",
        "【 교 재 】",
        "【교재】",
        "[Reference]",
        "Textbook:",
        "Reference:",
        "Optional:",
    ]

    for prefix in noise_prefixes:
        text = text.replace(prefix, " ")

    text = normalize_spacing(text)

    if text.strip().lower() in NULL_LIKE_VALUES:
        return ""

    return text


def add_normalized_columns(
    df: pd.DataFrame,
    text_fields: list[str],
    textbook_fields: set[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    textbook_fields = textbook_fields or set()

    """
    기존의 컬럼을 정규화된 명칭으로 변경
    """
    result = df.copy()
    field_stats: dict[str, Any] = {}

    for field in text_fields:
        if field not in result.columns:
            field_stats[field] = {
                "exists": False,
                "non_empty_original": 0,
                "non_empty_clean": 0,
            }
            continue

        clean_col = f"{field}_clean"
        match_col = f"{field}_match"

        if field in textbook_fields:
            result[clean_col] = result[field].apply(clean_textbook_noise)
        else:
            result[clean_col] = result[field].apply(clean_basic_text)

        result[match_col] = result[clean_col].apply(normalize_for_match)

        field_stats[field] = {
            "exists": True,
            "non_empty_original": int((result[field].astype(str).str.strip() != "").sum()),
            "non_empty_clean": int((result[clean_col].astype(str).str.strip() != "").sum()),
            "emptied_by_cleaning": int(
                (
                    (result[field].astype(str).str.strip() != "")
                    & (result[clean_col].astype(str).str.strip() == "")
                ).sum()
            ),
        }

    return result, field_stats


def build_report(
    curriculum_original: pd.DataFrame,
    curriculum_normalized: pd.DataFrame,
    curriculum_field_stats: dict[str, Any],
    resources_original: pd.DataFrame,
    resources_normalized: pd.DataFrame,
    resource_field_stats: dict[str, Any],
) -> dict[str, Any]:
    return {
        "status": "success",
        "curriculum_courses": {
            "input_rows": int(len(curriculum_original)),
            "output_rows": int(len(curriculum_normalized)),
            "input_columns": int(len(curriculum_original.columns)),
            "output_columns": int(len(curriculum_normalized.columns)),
            "field_stats": curriculum_field_stats,
        },
        "learning_resources": {
            "input_rows": int(len(resources_original)),
            "output_rows": int(len(resources_normalized)),
            "input_columns": int(len(resources_original.columns)),
            "output_columns": int(len(resources_normalized.columns)),
            "field_stats": resource_field_stats,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Step 2 - Normalize raw text fields for topic extraction."
    )

    parser.add_argument(
        "--curriculum",
        type=Path,
        default=Path("curriculum-data/processed/university_syllabus_eda_cleaned_final.csv"),
    )
    parser.add_argument(
        "--resources",
        type=Path,
        default=Path("curriculum-data/processed/learning_resource_refactor.csv"),
    )
    parser.add_argument(
        "--output-curriculum",
        type=Path,
        default=Path("scripts/topic_pipeline/data/processed/curriculum_courses_normalized.csv"),
    )
    parser.add_argument(
        "--output-resources",
        type=Path,
        default=Path("scripts/topic_pipeline/data/processed/learning_resources_normalized.csv"),
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=Path("scripts/topic_pipeline/data/processed/normalization_report.json"),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    args.output_curriculum.parent.mkdir(parents=True, exist_ok=True)
    args.output_resources.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.parent.mkdir(parents=True, exist_ok=True)

    curriculum_df = read_csv_safely(args.curriculum)
    resources_df = read_csv_safely(args.resources)

    curriculum_normalized, curriculum_field_stats = add_normalized_columns(
        curriculum_df,
        CURRICULUM_TEXT_FIELDS,
        textbook_fields={"main_textbook", "reference_material"},
    )

    resources_normalized, resource_field_stats = add_normalized_columns(
        resources_df,
        RESOURCE_TEXT_FIELDS,
    )

    curriculum_normalized.to_csv(
        args.output_curriculum,
        index=False,
        encoding="utf-8-sig",
    )

    resources_normalized.to_csv(
        args.output_resources,
        index=False,
        encoding="utf-8-sig",
    )

    report = build_report(
        curriculum_original=curriculum_df,
        curriculum_normalized=curriculum_normalized,
        curriculum_field_stats=curriculum_field_stats,
        resources_original=resources_df,
        resources_normalized=resources_normalized,
        resource_field_stats=resource_field_stats,
    )

    with args.output_report.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("=" * 80)
    print("Topic Pipeline Step 2 - Normalize Text")
    print("=" * 80)
    print("Status: success")
    print(f"Curriculum output : {args.output_curriculum}")
    print(f"Resources output  : {args.output_resources}")
    print(f"Report output     : {args.output_report}")

    print("\nCurriculum field stats:")
    for field, stat in curriculum_field_stats.items():
        print(
            f"- {field}: "
            f"exists={stat['exists']}, "
            f"original_non_empty={stat['non_empty_original']}, "
            f"clean_non_empty={stat['non_empty_clean']}, "
            f"emptied={stat['emptied_by_cleaning']}"
        )

    print("\nLearning resource field stats:")
    for field, stat in resource_field_stats.items():
        print(
            f"- {field}: "
            f"exists={stat['exists']}, "
            f"original_non_empty={stat['non_empty_original']}, "
            f"clean_non_empty={stat['non_empty_clean']}, "
            f"emptied={stat['emptied_by_cleaning']}"
        )


if __name__ == "__main__":
    main()
