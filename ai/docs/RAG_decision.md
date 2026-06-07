# RAG 파이프라인 구축 - 의사결정 문서 (Day 2)

> WhereToGo 교육 컨설턴트 AI - RAG 시스템 설계 의사결정 기록
> 작성 목적: 코드 구현 전 핵심 설계 결정사항 확정 및 공유

---

## 1. 개요

### 1.1 목표
사용자 학습 목표 기반 커리큘럼 생성을 위한 RAG 검색 시스템 구축

### 1.2 데이터 현황
| 데이터셋 | 건수 | 검색 텍스트 평균 | 최대 길이 |
|----------|------|------------------|-----------|
| learning_resources | 123건 | 647자 | 3,132자 |
| curriculum_courses | 1,663건 | 319자 | 2,442자 |

### 1.3 핵심 결론
- 모든 문서가 임베딩 모델 한계(8,191토큰) 내 → **청킹 불필요**
- **No-Chunking + Metadata Enrichment** 전략 채택

---

## 2. 기술 스택 확정

| 구성요소 | 선택 | 비고 |
|----------|------|------|
| Vector DB | ChromaDB | 로컬, MVP 적합 |
| 저장 방식 | Persistent | ./chroma_db 디스크 저장 |
| 임베딩 모델 | OpenAI text-embedding-3-small | 1536차원, 가성비 |
| 거리 함수 | cosine | 텍스트 검색 표준 |
| 컬렉션 구조 | 다중 (2개) | courses / resources |

---

## 3. 핵심 설계 전략

### 3.1 문서 변환 전략 (Enrichment)

**정의:** 흩어진 필드 정보를 검색 텍스트에 통합하여 검색 정밀도 향상

- 메타데이터 = 필터링용 (임베딩 안 됨)
- 검색 텍스트 = 임베딩 대상 (맥락 정보 포함)
- 과목명/학과/토픽 등을 텍스트에 포함하여 다양한 검색어와 매칭

### 3.2 청킹 전략
- 청킹하지 않음 (각 row = 하나의 검색 문서)
- 근거: 데이터의 99% 이상이 1,000자 이하

---

## 4. ID 전략

### 4.1 curriculum_courses
- 형식: `course_{source_row_number}`
- 예시: `course_537`

### 4.2 learning_resources
- 형식: `resource_{source_type}_{external_id}`
- 예시: `resource_KOCW_12345`

### 4.3 목적
- 결정론적 ID → 재인덱싱 시 중복 방지 (upsert 가능)

---

## 5. RAG 문서 스키마

### 5.1 curriculum_courses

#### 임베딩 텍스트 (벡터화 대상)

```plain text
[대학 강의계획서]

과목명: {course_name}
학과: {department_name}
학년/학기: {grade}학년 {semester}
학점: {credit}

학습 목표:
{learning_objective}

선수지식:
{prerequisite_material}

주교재:
{main_textbook}

연결 토픽:
{mapped_topic_names}
```

#### 메타데이터 (필터링용)
| 필드명 | 타입 | 용도 |
|--------|------|------|
| doc_type | str | 'course' 구분 |
| source_row_number | int | 원본 추적 (조인 키) |
| university_name | str | 대학 정보 |
| college_name | str | 단과대 정보 |
| department_name | str | 학과 필터 |
| course_name | str | 표시/검색 |
| grade | int | 학년 범위 필터 |
| semester | str | 학기 필터 |
| credit | int | 학점 정보 |
| has_prerequisite | bool | 선수과목 유무 |
| estimated_difficulty | str | 학년 기반 난이도 추정 |
| topic_names | str | 토픽(콤마 구분) |

#### 원본 필드 타입/용도 정리
| 필드명 | 타입 | 용도 |
|--------|------|------|
| source_row_number | int | 강의 고유 번호 (조인 키) |
| university_name | str | 대학명 |
| college_name | str | 단과대명 |
| department_name | str | 학과명 |
| course_name | str | 과목명 |
| grade | int | 학년 |
| semester | str | 학기 |
| credit | int | 학점 |
| learning_objective | str | 학습목표 (임베딩 중요 필드) |
| main_textbook | str | 주 교재 |
| sub_textbook | str | 보조 교재 |
| reference_material | str | 참고자료 |
| prerequisite_material | str | 선수 과목/지식 (없는 경우 존재) |
| keep_reason | str | 데이터 검수 시 보존 사유 (인덱싱 제외) |

---

### 5.2 learning_resources

#### 임베딩 텍스트 (벡터화 대상)
```text
[학습 자료]

자료명: {title}
분야: {main_category} > {sub_category}
난이도: {difficulty_level}
자료 유형: {content_type}
제공처: {provider_name}
교수자: {instructor_name}

설명:
{description}

연결 토픽:
{mapped_topic_names}
```

#### 메타데이터 (필터링용)
| 필드명 | 타입 | 용도 |
|--------|------|------|
| source_type | str | KOCW/KMOOC 필터 |
| external_id | str | 원본 추적 (조인 키) |
| title | str | 표시/검색 |
| main_category | str | 대분류 필터 |
| sub_category | str | 중분류 필터 |
| difficulty_level | str | 난이도 필터 (핵심) |
| content_type | str | 자료유형 필터 (video/document/etc) |
| provider_name | str | 제공처 정보 |
| instructor_name | str | 교수자 정보 |
| topic_names | str | 토픽(콤마 구분) |
| url | str | 참조 링크 |

#### 원본 필드 타입/용도 정리
| 필드명 | 타입 | 용도 |
|--------|------|------|
| source_type | str | 제공 출처 (KOCW, KMOOC) |
| external_id | str | 자료 고유 코드 (조인 키) |
| title | str | 자료명 |
| main_category | str | 대분류 |
| sub_category | str | 중분류 |
| difficulty_level | str | 난이도 (beginner/intermediate/advanced/unknown) |
| content_type | str | 자료유형 (video/document/etc) |
| provider_name | str | 제공처 |
| instructor_name | str | 교수자 |
| description | str | 자료 설명 |

#### 난이도(difficulty_level) 현황
- 타입: str, 범주형
- 값: beginner / intermediate / advanced / unknown
- unknown 비율: 약 123건 중 21건

---

## 6. 토픽 매핑 결합 전략 (사전 결합)

### 6.1 방식
인덱싱 전 매핑 CSV를 사전 결합하여 원본에 topic_names 컬럼 추가

### 6.2 조인 키

| 매핑 파일 | 매핑 측 키 | 원본 측 키 |
|-----------|-----------|-----------|
| final_course_topics_import.csv | curriculum_course_lookup_key | curriculum_courses.source_row_number |
| final_resource_topics_import.csv | learning_resource_lookup_key | learning_resources.external_id |

### 6.3 처리 로직
1. 매핑 CSV 로드
2. 조인 키별 토픽 리스트 집계 (다대다 → 콤마 구분 문자열)
3. 원본 데이터에 topic_names 컬럼 추가
4. 결합된 데이터로 인덱싱

---

## 7. 검색 전략

### 7.1 멀티 컬렉션 통합 검색 (옵션 C: 용도별 분리 반환)

#### 방식
courses와 resources를 각각 검색하여 용도별로 분리 반환

#### 반환 구조
```python
{
    "courses": [    # curriculum_step_courses용 (참고 과목)
        {"course_name": "자료구조", "score": 0.89, "metadata": {...}},
        ...
    ],
    "resources": [  # curriculum_step_resources용 (추천 자료)
        {"title": "파이썬 자료구조 강의", "score": 0.91, "metadata": {...}},
        ...
    ]
}
```

#### 근거
- ERD상 curriculum_step_courses(참고 과목)와 curriculum_step_resources(추천 자료)가 별도 테이블
- LLM이 용도를 구분하여 활용하기 용이

### 7.2 검색 방식
- Phase 1 (MVP): Dense Retrieval + 수동 메타데이터 필터
- 필터 파라미터 인터페이스는 열어둠 (추후 Agent 활용 대비)

### 7.3 Top-K
- 기본값 K=5~10 (파라미터로 조절 가능)

---

## 8. Self-Query 전략

### 8.1 MVP 단계
- 미구현
- 기본 Dense 검색 + 수동 필터 파라미터만 제공

### 8.2 추후 (LangGraph 통합 시)
- Agent가 면담 컨텍스트 기반으로 필터 추출 여부 결정
- 검색 도구 호출 시 필터 포함/제외 선택

### 8.3 발동 조건 (추후 적용)
- 검색 결과 품질 저하 시 (결과 수 부족, 점수 낮음)
- 사용자 입력 부족/모호 시
- → Agent 판단에 위임

---

## 9. 리랭킹 전략

### 9.1 MVP 단계
- 미적용 (기본 검색 우선)

### 9.2 추후 결정
- 검색 테스트 후 품질 평가
- 필요시 MMR(Maximum Marginal Relevance) 추가
  - 관련성 + 다양성 균형
  - 커리큘럼 단계별 다양한 강의 확보에 유리

---

## 10. 메타데이터 처리 주의사항 (ChromaDB 제약)

| 제약 | 처리 방법 |
|------|-----------|
| 허용 타입: str/int/float/bool만 | 그 외 타입 변환 필요 |
| None 값 불가 | 빈 문자열('') 또는 기본값 대체 |
| 리스트 불가 | topic_names는 "토픽1,토픽2" 문자열로 |

---

## 11. 예외 케이스 처리

| 케이스 | 해당 데이터 | 처리 방법 |
|--------|-------------|-----------|
| 짧은 문서 (100자 이하) | courses 168건 | 교재 정보 추가 보강 |
| 긴 문서 (2000자 이상) | resources 7건 | 현재 상태 유지 (모니터링) |
| 빈 필드 (prerequisite 등) | 다수 | 텍스트에서 생략, has_xxx 플래그 표시 |
| 난이도 unknown | resources 21건 | unknown 그대로 유지 |

---

## 12. 인덱싱 파이프라인 흐름

```
[입력]
├── learning_resources.csv (123건)
├── curriculum_courses.csv (1,663건)
├── final_course_topics_import.csv (토픽 매핑)
└── final_resource_topics_import.csv (토픽 매핑)

        ↓
[토픽 사전 결합]
├── 조인 키로 토픽 집계 → topic_names 컬럼 추가

        ↓
[전처리]
├── 결측값 처리 (빈 문자열 통일)
├── 텍스트 정규화
└── 필드 타입 변환 (grade → int 등)

        ↓
[문서 변환]
├── transform_curriculum_course() → 임베딩텍스트 + 메타데이터
└── transform_learning_resource() → 임베딩텍스트 + 메타데이터

        ↓
[임베딩]
└── OpenAI text-embedding-3-small (배치 처리)

        ↓
[ChromaDB 저장 (Persistent)]
├── Collection: courses (1,663개)
└── Collection: resources (123개)

        ↓
[검증]
├── 문서 수 일치 확인
├── 임베딩 차원 확인 (1536)
└── 샘플 검색 테스트
```

---

## 13. 미결정/추후 확정 사항

| 항목 | 상태 | 결정 시점 |
|------|------|-----------|
| 리랭킹(MMR) 적용 여부 | 보류 | 검색 테스트 후 |
| Self-Query 발동 로직 | 보류 | LangGraph 통합 시 |
| 증분 업데이트(upsert) | 보류 | 데이터 갱신 필요 시 |
| 프로덕션 Vector DB 전환 | 보류 | 배포 단계 |

---

## 14. Task별 체크리스트

- [ ] ChromaDB Persistent 설정 (cosine, 2개 컬렉션)
- [ ] 임베딩 함수 구현 (배치 처리, 재시도 로직)
- [ ] 토픽 매핑 사전 결합 로직
- [ ] 문서 변환 함수 (courses/resources)
- [ ] 인덱싱 스크립트 작성
- [ ] 인덱싱 실행 및 검증
- [ ] 검색 함수 구현 (용도별 분리 반환)
- [ ] 검색 테스트 (다양한 쿼리셋)
```