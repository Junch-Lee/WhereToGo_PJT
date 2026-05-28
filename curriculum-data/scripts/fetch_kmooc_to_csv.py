import csv
import os
import time
import json
import re
import html
from pathlib import Path
from urllib.parse import unquote

import requests
import dotenv

dotenv.load_dotenv()

"""
fetch_kmooc_to_csv.py

K-MOOC courseList_v2_0 -> courseDetail_v2_0 보강 -> KOCW와 동일 컬럼 CSV 생성
- 접근 불가능한 강좌(resultCode=11 등) 자동 제외
- summary(강좌 소개) 내 HTML, 이모지, URL, 이메일, 특수문자, 개인정보 완벽 정제
"""

BASE_URL = "https://apis.data.go.kr/B552881/kmooc_v2_0"
LIST_ENDPOINT = f"{BASE_URL}/courseList_v2_0"
DETAIL_ENDPOINT = f"{BASE_URL}/courseDetail_v2_0"

API_KEY = os.getenv("KMOOC_API_KEY", "여기에_발급받은_SERVICE_KEY_입력")

OUT_PATH = Path("processed/learning_resources_kmooc.csv")

START_PAGE = 1
END_PAGE = 30
PAGE_SIZE = 30

FETCH_DETAIL = True
DETAIL_SLEEP_SECONDS = 0.2
PAGE_SLEEP_SECONDS = 0.3

TARGET_KEYWORDS = [
    "컴퓨터", "소프트웨어", "프로그래밍", "파이썬", "Python", "자바", "Java",
    "웹", "데이터", "데이터베이스", "SQL", "알고리즘", "자료구조", "인공지능",
    "AI", "머신러닝", "딥러닝", "네트워크", "운영체제", "정보보안", "클라우드", "빅데이터",
]

# 절대 변경하지 않는 최종 컬럼명
FIELDNAMES = [
    "source_type", "external_id", "main_category", "sub_category", "title",
    "description", "provider_name", "instructor_name", "difficulty_level",
    "semester", "url", "thumbnail_url", "syllabus_url", "content_type",
    "view_count", "popular_score",
]

DEBUG_DETAIL_SAVED = False


def clean_text_and_html(raw_text):
    """HTML 태그, URL, 이메일, 이모지, 특정 특수문자 등을 모두 정제하는 함수"""
    if not raw_text:
        return ""
    
    # 1. HTML 엔티티 디코딩 (&nbsp; -> 공백 등)
    text = html.unescape(raw_text)
    
    # 2. HTML 태그 제거
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # 3. URL 제거 (http 또는 https로 시작하는 링크)
    text = re.sub(r'https?://\S+', '', text)
    
    # 4. 이메일 주소 제거
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', text)
    
    # 5. 개인정보(조교 이름 등) 및 불필요한 라벨 제거
    text = re.sub(r'[가-힣]{2,4}\s*조교', '', text) # 예: '김교령 조교' 제거
    text = re.sub(r'(?i)e-mail\s*:', '', text) # 대소문자 구분 없이 'e-mail:' 제거
    
    # 6. 지정된 특수문자 및 따옴표, 슬래시 제거
    text = re.sub(r'[◆●"\'/]', ' ', text)
    
    # 7. 이모지 제거 (대부분의 이모지가 포함된 유니코드 확장 영역)
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    
    # 8. 연속된 공백이나 줄바꿈을 하나의 공백으로 깔끔하게 정리
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def normalize_text(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()


def pick(data, candidates):
    if not isinstance(data, dict):
        return ""

    for key in candidates:
        if key in data and data[key] not in (None, ""):
            return normalize_text(data[key])

    lowered = {str(k).lower(): k for k in data.keys()}
    for key in candidates:
        found_key = lowered.get(str(key).lower())
        if found_key is not None and data[found_key] not in (None, ""):
            return normalize_text(data[found_key])

    compacted = {str(k).lower().replace("_", ""): k for k in data.keys()}
    for key in candidates:
        found_key = compacted.get(str(key).lower().replace("_", ""))
        if found_key is not None and data[found_key] not in (None, ""):
            return normalize_text(data[found_key])

    return ""


def to_int(value):
    try:
        value = normalize_text(value)
        if value == "":
            return ""
        return int(float(value.replace(",", "")))
    except Exception:
        return ""


def to_float(value):
    try:
        value = normalize_text(value)
        if value == "":
            return ""
        return float(value)
    except Exception:
        return ""


def infer_difficulty(title, description):
    text = f"{title} {description}"

    beginner_keywords = ["입문", "기초", "개론", "처음", "초급", "리터러시", "기본 개념"]
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
            row.get("provider_name", ""),
        ]
    ).lower()

    return any(keyword.lower() in text for keyword in TARGET_KEYWORDS)


def request_json(url, params, max_retries=3):
    decoded_key = unquote(API_KEY)
    key_variations = [
        ("ServiceKey", API_KEY),
        ("ServiceKey", decoded_key),
        ("serviceKey", API_KEY),
        ("serviceKey", decoded_key)
    ]

    last_error = None

    for key_name, key_val in key_variations:
        params_with_key = dict(params)
        params_with_key[key_name] = key_val

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(
                    url,
                    params=params_with_key,
                    timeout=(5, 50),
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                response.raise_for_status()
                return response.json()

            except requests.exceptions.JSONDecodeError:
                print(f"  JSON 파싱 실패 (키 변형: {key_name})")
                return None

            except requests.exceptions.ReadTimeout:
                print(f"  Timeout 발생, 재시도 {attempt}/{max_retries}")
                time.sleep(2)

            except requests.exceptions.RequestException as error:
                last_error = error
                time.sleep(1)

    print(f"  최종 요청 실패: {last_error}")
    return None


def find_course_list(payload):
    if payload is None:
        return []

    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if not isinstance(payload, dict):
        return []

    common_paths = [
        ("data",),
        ("results",),
        ("items",),
        ("item",),
        ("response", "body", "items"),
        ("response", "body", "items", "item"),
        ("body", "items"),
        ("body", "items", "item"),
    ]

    for path in common_paths:
        current = payload
        for key in path:
            if not isinstance(current, dict) or key not in current:
                current = None
                break
            current = current[key]

        if isinstance(current, list):
            return [item for item in current if isinstance(item, dict)]

        if isinstance(current, dict):
            nested_item = current.get("item")
            if isinstance(nested_item, list):
                return [item for item in nested_item if isinstance(item, dict)]

    candidates = []

    def walk(obj):
        if isinstance(obj, list):
            dict_items = [item for item in obj if isinstance(item, dict)]
            if dict_items:
                candidates.append(dict_items)
        elif isinstance(obj, dict):
            for value in obj.values():
                walk(value)

    walk(payload)

    if not candidates:
        return []

    candidates.sort(key=len, reverse=True)
    return candidates[0]


def find_detail_dict(payload):
    if payload is None:
        return {}

    if isinstance(payload, dict):
        results = payload.get("results")
        if isinstance(results, dict):
            return results
        if isinstance(results, list) and len(results) > 0 and isinstance(results[0], dict):
            return results[0]

        for key in ["data", "result", "item", "detail"]:
            value = payload.get(key)
            if isinstance(value, dict):
                return value

        response = payload.get("response")
        if isinstance(response, dict):
            body = response.get("body", {})
            if isinstance(body, dict):
                items = body.get("items")
                if isinstance(items, dict):
                    item = items.get("item")
                    if isinstance(item, dict):
                        return item
                    if isinstance(item, list) and item and isinstance(item[0], dict):
                        return item[0]

        return payload

    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        return payload[0]

    return {}


def fetch_course_list(page):
    params = {
        "page": str(page),
        "size": str(PAGE_SIZE),
        "pageNo": str(page),
        "numOfRows": str(PAGE_SIZE),
    }

    print(f"K-MOOC 목록 API 호출 중: page={page}, size={PAGE_SIZE}")
    payload = request_json(LIST_ENDPOINT, params)

    if payload is None:
        return []

    courses = find_course_list(payload)
    print(f"  목록 응답에서 {len(courses)}개 후보 추출")
    return courses


def fetch_course_detail(external_id):
    global DEBUG_DETAIL_SAVED
    
    if not external_id:
        return None

    params = {"CourseId": str(external_id)}
    payload = request_json(DETAIL_ENDPOINT, params, max_retries=2)
    
    if payload:
        result_code = payload.get("resultCode") or payload.get("header", {}).get("resultCode")
        result_msg = payload.get("resultMsg") or payload.get("header", {}).get("resultMsg")
        
        if result_code and str(result_code) not in ("00", "200", "SUCCESS", "0"):
            print(f"  ⚠️ [API 논리 에러 감지] resultCode: {result_code}, resultMsg: {result_msg}")
            return None 
        
        if not DEBUG_DETAIL_SAVED:
            debug_filename = f"debug_kmooc_detail_{external_id}.json"
            with open(debug_filename, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            print(f"  [디버깅] 상세 응답 결과가 {debug_filename} 에 저장되었습니다.")
            DEBUG_DETAIL_SAVED = True

        detail = find_detail_dict(payload)
        if detail:
            return detail

    return None


def merge_prefer_detail(list_item, detail_item):
    merged = dict(list_item)

    if isinstance(detail_item, dict):
        for key, value in detail_item.items():
            if value not in (None, ""):
                merged[key] = value

    return merged


def normalize_course(raw):
    external_id = pick(
        raw,
        ["course_id", "courseId", "course_key", "courseKey", "id", "class_id", "classId"],
    )

    title = pick(
        raw,
        ["course_name", "courseName", "name", "title", "class_name", "className", "강좌명"],
    )

    description = pick(
        raw,
        [
            "summary", "course_description", "courseDescription", "description", "overview",
            "intro", "short_description", "강좌설명", "강좌소개",
        ],
    )
    
    # 💡 강화된 텍스트 정제 함수 적용
    description = clean_text_and_html(description)

    keywords = pick(raw, ["keyword", "keywords", "course_keyword", "courseKeyword", "tags", "분야"])
    if keywords:
        clean_keywords = clean_text_and_html(keywords)
        if clean_keywords and clean_keywords not in description:
            description = f"{description} 키워드: {clean_keywords}".strip()

    main_category = pick(
        raw,
        [
            "classfy_name", "classfyName", "main_category", "mainCategory", "category", 
            "category_name", "categoryName", "field", "classfy", "분류", "대분류",
        ],
    )

    sub_category = pick(
        raw,
        [
            "middle_classfy_name", "middleClassfyName", "sub_category", "subCategory", 
            "subcategory", "subject", "subject_name", "subjectName", "middle_category", 
            "middleCategory", "중분류", "소분류",
        ],
    )

    if main_category and ">" in main_category and not sub_category:
        parts = [part.strip() for part in main_category.split(">") if part.strip()]
        main_category = parts[0] if parts else ""
        sub_category = parts[-1] if len(parts) >= 2 else ""

    provider_name = pick(
        raw,
        [
            "org_name", "orgName", "organization", "organization_name", "institution",
            "provider", "univ_name", "univName", "운영기관", "기관명",
        ],
    )

    instructor_name = pick(
        raw,
        [
            "teacher", "teachers", "instructor", "instructors", "professor",
            "professor_name", "교수자", "교수명",
        ],
    )

    semester = pick(
        raw,
        [
            "semester", "term", "run", "year", "course_start", "courseStart",
            "start_date", "startDate", "운영기간", "개강일", "study_start"
        ],
    )

    course_url = pick(
        raw,
        ["course_url", "courseUrl", "url", "homepage", "class_url", "classUrl", "강좌URL"],
    )

    thumbnail_url = pick(
        raw,
        [
            "thumbnail_url", "thumbnailUrl", "image", "image_url", "imageUrl",
            "course_image", "courseImage", "강좌이미지", "썸네일",
        ],
    )

    syllabus_url = pick(
        raw,
        ["syllabus_url", "syllabusUrl", "plan_url", "planUrl", "강의계획서"],
    )

    content_type = pick(
        raw,
        ["content_type", "contentType", "type", "media_type", "mediaType"],
    ) or "online"

    view_count = pick(raw, ["view_count", "viewCount", "views", "hit", "hits", "조회수"])
    popular_score = pick(raw, ["popular_score", "popularScore", "rating", "score", "평점"])

    return {
        "source_type": "KMOOC",
        "external_id": external_id,
        "main_category": main_category,
        "sub_category": sub_category,
        "title": title,
        "description": description,
        "provider_name": provider_name,
        "instructor_name": instructor_name,
        "difficulty_level": infer_difficulty(title, description),
        "semester": semester,
        "url": course_url,
        "thumbnail_url": thumbnail_url,
        "syllabus_url": syllabus_url,
        "content_type": content_type,
        "view_count": to_int(view_count),
        "popular_score": to_float(popular_score),
    }


def should_fetch_detail(row):
    if not FETCH_DETAIL:
        return False

    required_for_display = [
        "description", "main_category", "sub_category", 
        "url", "provider_name", "instructor_name", "thumbnail_url"
    ]
    return any(not row.get(field) for field in required_for_display)


def save_csv(rows):
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUT_PATH, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main():
    if not API_KEY or API_KEY == "여기에_발급받은_SERVICE_KEY_입력":
        raise RuntimeError(
            "KMOOC_API_KEY 환경변수를 설정하거나, 코드의 API_KEY 값을 발급받은 서비스키로 바꿔주세요."
        )

    all_rows = []
    seen = set()

    for page in range(START_PAGE, END_PAGE + 1):
        list_items = fetch_course_list(page)

        if not list_items:
            print("  이 페이지에서 목록 데이터가 없습니다.")
            time.sleep(PAGE_SLEEP_SECONDS)
            continue

        for list_item in list_items:
            base_row = normalize_course(list_item)

            if not base_row["title"]:
                continue

            if not contains_target_keyword(base_row):
                continue

            detail_item = {}
            if should_fetch_detail(base_row):
                print(f"  상세 API 보강 시도: {base_row['title']}")
                detail_item = fetch_course_detail(base_row["external_id"])
                time.sleep(DETAIL_SLEEP_SECONDS)
                
                if detail_item is None:
                    print(f"  ❌ 접근 불가 강좌 제외됨: {base_row['title']}")
                    continue

            merged_raw = merge_prefer_detail(list_item, detail_item)
            row = normalize_course(merged_raw)

            if not row["title"]:
                continue

            if not contains_target_keyword(row):
                continue

            unique_key = row["external_id"] or f"{row['title']}_{row['provider_name']}"
            unique_key = f"KMOOC:{unique_key}"

            if unique_key in seen:
                continue

            seen.add(unique_key)
            all_rows.append(row)

        print(f"  현재 누적 저장 후보 수: {len(all_rows)}")
        time.sleep(PAGE_SLEEP_SECONDS)

    save_csv(all_rows)
    
    print()
    print(f"완료: {OUT_PATH}")
    print(f"최종 저장 강좌 수: {len(all_rows)}")
    print("컬럼:")
    print(",".join(FIELDNAMES))


if __name__ == "__main__":
    main()