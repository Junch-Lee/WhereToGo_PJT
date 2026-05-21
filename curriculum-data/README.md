# 커리큘럼 데이터셋 구축 안내

# 1. `learning_resources.csv` 구축

본 디렉토리는 웹 기반 커리큘럼 추천 서비스에서 사용할 초기 강좌 데이터셋을 수집·정제하기 위한 작업 공간입니다.

KOCW와 K-MOOC의 공개 API를 활용해 외부 강좌 데이터를 수집했고, 서로 다른 응답 구조를 하나의 공통 CSV 구조로 정규화했습니다.

---

## 1. 디렉토리 구조

```text
curriculum-data/
├── processed/
│   ├── debug/
│   │   ├── debug_kmooc_detail_19982.json
│   │   └── debug_kmooc_detail_20002.json
│   │
│   ├── learning_resources_columns.txt
│   ├── learning_resources_kmooc.csv
│   ├── learning_resources_kocw_ver2.csv
│   └── learning_resources.csv
│
├── raw/
│   └── university_syllabus.csv
│
├── scripts/
│   ├── venv/
│   ├── .env
│   ├── fetch_kmooc_to_csv.py
│   └── fetch_kocw_to_csv.py
│
└── requirements.txt
```

---

## 2. 데이터 출처

### KOCW

#### [KOCW 강의정보 API](https://www.riss.kr/apicenter/apiKocwInfo.do)에서 XML 형식의 공개 강의 데이터를 수집했습니다.

`scripts/fetch_kocw_to_csv.py`는 KOCW API 응답 XML을 파싱하여 공통 CSV 컬럼 구조로 변환합니다.

주요 수집 필드:

```text
course_id
course_title
course_description
course_keyword
lecturer
provider
term
course_url
thumbnail_url
syllabus_url
content_type
view_count
popular_score
```

---

### K-MOOC

#### [K-MOOC 강좌정보 API](https://www.data.go.kr/data/15042355/openapi.do#/API%20%EB%AA%A9%EB%A1%9D/courseList_v2_0)에서 JSON 형식의 온라인 공개강좌 데이터를 수집했습니다.

활용한 종단점(`GET`):

```text
courseList_v2_0    # 강좌 목록 조회
courseDetail_v2_0  # 강좌 상세 정보 조회
```

수집 절차:

```text
1. courseList_v2_0으로 강좌 목록 조회
2. 강좌 ID, 제목, 기관, 교수자, URL 등 기본 정보 추출
3. courseDetail_v2_0으로 상세 정보 보강
4. 대분류, 중분류, 강좌 소개 정보 추가
5. KOCW와 동일한 CSV 컬럼 구조로 저장
```

주요 상세 필드:

```text
id
name
summary
classfy_name
middle_classfy_name
url
course_image
org_name
professor
study_start
study_end
```

---

## 3. 공통 CSV 구조

KOCW와 K-MOOC는 모두 추천 가능한 학습 리소스이므로 동일한 컬럼 구조로 정규화했습니다.

```csv
source_type,external_id,main_category,sub_category,title,description,provider_name,instructor_name,difficulty_level,semester,url,thumbnail_url,syllabus_url,content_type,view_count,popular_score
```

| 컬럼명 | 설명 |
|---|---|
| source_type | 데이터 출처. `KOCW` 또는 `KMOOC` |
| external_id | 원본 API의 강좌 고유 ID |
| main_category | 대분류 |
| sub_category | 중분류 |
| title | 강좌명 |
| description | 강좌 설명 |
| provider_name | 제공 기관 |
| instructor_name | 교수자 |
| difficulty_level | 추정 난이도 |
| semester | 학기 또는 운영 기간 |
| url | 강좌 URL |
| thumbnail_url | 썸네일 URL |
| syllabus_url | 강의계획서 URL |
| content_type | 콘텐츠 유형 |
| view_count | 조회수 |
| popular_score | 평점 또는 인기 점수 |

---

## 4. 생성 파일

### `processed/learning_resources_kocw.csv`

KOCW API에서 수집한 강좌 데이터입니다.

### `processed/learning_resources_kmooc.csv`

K-MOOC API에서 수집한 강좌 데이터입니다.

### `processed/learning_resources.csv`

KOCW와 K-MOOC 데이터를 병합한 최종 데이터셋입니다. Django 서버의 초기 `LearningResource` 데이터 적재에 사용됩니다.

병합 기준:

```text
1. 컬럼명과 컬럼 순서 통일
2. source_type으로 출처 구분
3. source_type + external_id 기준 중복 제거
4. utf-8-sig 인코딩으로 저장
```

---

## 5. 실행 방법

필요 패키지 설치:

```bash
pip install -r requirements.txt
```

`.env` 파일에 API Key 설정:

```env
KOCW_API_KEY=발급받은_KOCW_KEY
KMOOC_API_KEY=발급받은_KMOOC_SERVICE_KEY
```

KOCW 데이터 수집:

```bash
python scripts/fetch_kocw_to_csv.py
```

K-MOOC 데이터 수집:

```bash
python scripts/fetch_kmooc_to_csv.py
```

수집된 CSV는 `processed/` 디렉토리에 저장됩니다.

---

## 6. 필터링 기준

초기 MVP에서는 전체 강좌가 아닌 SW/AI/데이터/웹 관련 강좌를 우선 수집했습니다.

주요 필터링 키워드:

```text
컴퓨터
소프트웨어
프로그래밍
파이썬
Java
웹
데이터
데이터베이스
SQL
알고리즘
자료구조
인공지능
AI
머신러닝
딥러닝
네트워크
운영체제
정보보안
클라우드
빅데이터
```

---

## 7. Django 서버 활용

최종 생성된 `processed/learning_resources.csv`는 Django 서버의 초기 데이터 적재 파일로 사용됩니다.

적재 후 REST API를 통해 강좌 목록, 상세 조회, 검색 기능을 구현할 수 있습니다.

예상 API:

```text
GET /api/courses/resources/
GET /api/courses/resources/{id}/
GET /api/courses/resources/?q=인공지능
GET /api/courses/resources/?source_type=KMOOC
GET /api/courses/resources/?source_type=KOCW
```

---

## 8. 향후 확장 방향

```text
1. KOCW/K-MOOC 수집 범위 확대
2. 대학학과커리큘럼 데이터 추가
3. 강의계획서 기반 주차별 학습 내용 추출
4. 강좌별 토픽 태깅
5. 난이도 추정 로직 개선
6. 사용자 목표 기반 추천 점수 계산
7. AI 기반 커리큘럼 추천 로직 연동
```

---

## 요약

KOCW와 K-MOOC API를 통해 외부 강좌 데이터를 수집하고, 서로 다른 응답 구조를 하나의 `learning_resources.csv` 구조로 정규화했습니다.

이 데이터셋은 Django RESTful API 서버의 초기 강좌 데이터로 활용되며, 이후 AI 기반 커리큘럼 추천 시스템의 추천 후보 데이터로 확장될 수 있습니다.



# 2. `curriculum_cources.csv`

`curriculum_courses.csv`는 대학 강의계획서 데이터를 기반으로 만든 커리큘럼 데이터셋이다.  
사용자가 전공, 학년, 학기, 과목명 등을 기준으로 커리큘럼을 조회하고, 이후 학습 자료 추천이나 선수지식 분석에 활용할 수 있도록 구성했다.

### 데이터 출처

원본 데이터는 `한국교육학술정보원_대학학과커리큘럼_강의계획서_20221227.csv`를 사용했다.

- 제공기관: 한국교육학술정보원
- 데이터 내용: 대학별 학과 커리큘럼 및 강의계획서
- 원본 인코딩: `cp949`
- 추출 기준: `단과대학명 == "공과대학"`
- 추출 결과: `9,130`행

원본에서는 `공과대학` 값이 `학부 과명`이 아니라 `단과대학명` 컬럼에 존재하므로, 해당 컬럼을 기준으로 필터링했다.

### 생성한 CSV

추출한 데이터는 프로젝트 루트의 `engineering_curriculum_courses.csv`로 저장했다.  
DB import와 API 응답에서 사용하기 쉽도록 원본 한글 컬럼명을 영어 snake_case로 변환했다.

| 원본 컬럼 | 저장 컬럼 |
| --- | --- |
| 연도 | year |
| 대학교명 | university_name |
| 단과대학명 | college_name |
| 학부 과명 | department_name |
| 과목명 | course_name |
| 학년 | grade |
| 학기 | semester |
| 학점 | credit |
| 이론시간 | lecture_hours |
| 실습시간 | practice_hours |
| 과목구분 | course_type |
| 학습목표 | description |
| 주교재 | main_textbook |
| 부교재 | sub_textbook |
| 참고자료 | reference_material |
| 선행학습자료 | prerequisite_material |

추가로 `source_row_number`를 저장해 원본 CSV의 행 위치를 추적하고, 재import 시 중복 생성을 방지했다.

### DB 반영

기존 `CurriculumCourse` 모델은 기본 과목 정보만 담고 있었기 때문에, 강의계획서 데이터를 저장할 수 있도록 학교명, 단과대학명, 이론/실습 시간, 교재, 선수학습 자료 등의 필드를 추가했다.

`grade`는 숫자가 아닌 문자열로 저장한다. 원본 데이터에 `1`, `2`, `3`, `4`뿐 아니라 `전학년` 같은 값도 존재하기 때문이다.

### Import 방법

커리큘럼 CSV는 별도 management command로 DB에 저장한다.

```powershell
venv\Scripts\python.exe manage.py import_curriculum_courses engineering_curriculum_courses.csv
이 커맨드는 source_row_number를 기준으로 update_or_create를 수행하므로, 같은 CSV를 다시 import해도 중복 데이터가 계속 쌓이지 않는다.