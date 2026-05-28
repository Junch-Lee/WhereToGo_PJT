import csv
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path


API_URL = "http://www.kocw.net/home/api/handler.do"
API_KEY = "d42032ef87f4da7840f11973c864fd5cfdba0869c86446a9"

OUT_PATH = Path("processed/learning_resources_kocw.csv")

START_NUM = 1
END_NUM = 500
PAGE_SIZE = 10

TARGET_KEYWORDS = [
    "컴퓨터",
    "소프트웨어",
    "프로그래밍",
    "파이썬",
    "Python",
    "자바",
    "Java",
    "웹",
    "데이터",
    "데이터베이스",
    "SQL",
    "알고리즘",
    "자료구조",
    "인공지능",
    "AI",
    "머신러닝",
    "딥러닝",
    "네트워크",
    "운영체제",
]


def get_text(parent, tag_name):
    elem = parent.find(tag_name)

    if elem is None or elem.text is None:
        return ""

    return elem.text.strip()


def parse_taxon(taxon):
    """
    예:
    공학>전기ㆍ전자>전기전자공학

    반환:
    main_category = 공학
    sub_category = 전기전자공학
    """
    if not taxon:
        return "", ""

    parts = [part.strip() for part in taxon.split(">") if part.strip()]

    if not parts:
        return "", ""

    main_category = parts[0]
    sub_category = parts[-1] if len(parts) >= 2 else ""

    return main_category, sub_category


def infer_difficulty(title, description):
    text = f"{title} {description}"

    beginner_keywords = ["입문", "기초", "개론", "처음", "초급"]
    intermediate_keywords = ["활용", "실습", "설계", "분석"]
    advanced_keywords = ["고급", "심화", "응용", "캡스톤", "프로젝트", "최적화"]

    if any(keyword in text for keyword in beginner_keywords):
        return "beginner"

    if any(keyword in text for keyword in advanced_keywords):
        return "advanced"

    if any(keyword in text for keyword in intermediate_keywords):
        return "intermediate"

    return "unknown"


def contains_target_keyword(row):
    text = " ".join(
        [
            row.get("title", ""),
            row.get("description", ""),
            row.get("main_category", ""),
            row.get("sub_category", ""),
        ]
    ).lower()

    return any(keyword.lower() in text for keyword in TARGET_KEYWORDS)


def to_int(value):
    try:
        return int(str(value).replace(",", "").strip())
    except Exception:
        return ""


def to_float(value):
    try:
        return float(str(value).strip())
    except Exception:
        return ""


# 1-1. XML 파싱 함수 수정 (timeout 방지)
def fetch_xml(start_num, end_num, max_retries=3):
    params = {
        "key": API_KEY,
        "verb": "list_item",
        "category_type": "t",
        "category_id": "3",
        "from": "20100101",
        "to": "20260515",
        "start_num": str(start_num),
        "end_num": str(end_num),
    }

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                API_URL,
                params=params,
                timeout=(5, 60),
                headers={
                    "User-Agent": "Mozilla/5.0"
                },
            )
            response.raise_for_status()
            return response.content

        except requests.exceptions.ReadTimeout:
            print(f"  Timeout 발생: {start_num}~{end_num}, 재시도 {attempt}/{max_retries}")
            time.sleep(2)

        except requests.exceptions.RequestException as e:
            print(f"  요청 실패: {start_num}~{end_num}")
            print(f"  사유: {e}")
            return None

    print(f"  최종 실패: {start_num}~{end_num}")
    return None


def parse_xml(xml_content):
    root = ET.fromstring(xml_content)
    rows = []

    for item in root.findall(".//list_item"):
        course_id = get_text(item, "course_id")
        title = get_text(item, "course_title")
        lecturer = get_text(item, "lecturer")
        provider = get_text(item, "provider")
        term = get_text(item, "term")
        taxon = get_text(item, "taxon")
        course_description = get_text(item, "course_description")
        course_keyword = get_text(item, "course_keyword")
        course_url = get_text(item, "course_url")
        thumbnail_url = get_text(item, "thumbnail_url")
        syllabus_url = get_text(item, "syllabus_url")
        content_type = get_text(item, "content_type")
        view_count = get_text(item, "view_count")
        popular_score = get_text(item, "popular_score")

        if not title:
            continue

        main_category, sub_category = parse_taxon(taxon)

        description = course_description

        if course_keyword:
            description = f"{description}\n키워드: {course_keyword}".strip()

        row = {
            "source_type": "KOCW",
            "external_id": course_id,
            "main_category": main_category,
            "sub_category": sub_category,
            "title": title,
            "description": description,
            "provider_name": provider,
            "instructor_name": lecturer,
            "difficulty_level": infer_difficulty(title, description),
            "semester": term,
            "url": course_url,
            "thumbnail_url": thumbnail_url,
            "syllabus_url": syllabus_url,
            "content_type": content_type,
            "view_count": to_int(view_count),
            "popular_score": to_float(popular_score),
        }

        if contains_target_keyword(row):
            rows.append(row)

    return rows


def save_csv(rows):
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "source_type",
        "external_id",
        "main_category",
        "sub_category",
        "title",
        "description",
        "provider_name",
        "instructor_name",
        "difficulty_level",
        "semester",
        "url",
        "thumbnail_url",
        "syllabus_url",
        "content_type",
        "view_count",
        "popular_score",
    ]

    with open(OUT_PATH, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    all_rows = []
    seen = set()

    for start in range(START_NUM, END_NUM + 1, PAGE_SIZE):
        end = min(start + PAGE_SIZE - 1, END_NUM)

        print(f"KOCW API 호출 중: {start} ~ {end}")

        # 수정 1-2. xml_content가 없을 시 통과하게끔 구성(오류로 멈추는 것 방지)

        xml_content = fetch_xml(start, end)

        if xml_content is None:
            continue

        rows = parse_xml(xml_content)

        print(f"  필터링 후 {len(rows)}개 추출")

        for row in rows:
            unique_key = row["external_id"] or f"{row['title']}_{row['provider_name']}"

            if unique_key in seen:
                continue

            seen.add(unique_key)
            all_rows.append(row)

        time.sleep(0.3)

    save_csv(all_rows)

    print()
    print(f"완료: {OUT_PATH}")
    print(f"최종 저장 강좌 수: {len(all_rows)}")


if __name__ == "__main__":
    main()