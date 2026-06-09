# Node 2 (검색) 의사결정 확정 + 코드 생성 프롬프트

---

## 1. 확정 사항 요약

```
┌─────────────────────────────────────────────────────────────────┐
│              Node 2 의사결정 확정                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  N2-1 식별자  : course→source_row_number / resource→external_id│
│                 (LearningResource.lookup_key 저장 확인 필요)   │
│  N2-2 Topic   : metadata filter X → topic keyword query 보강   │
│  N2-3 선수지식 : 단일 검색, prerequisite는 query 보강만        │
│  N2-4 필터    : resources만 difficulty / courses 무필터        │
│  N2-5 Top-K   : courses=5, resources=8                         │
│  N2-6 scope   : false면 검색 스킵 + 빈 결과                    │
│                                                                 │
│  핵심 원칙: 기존 searcher 재사용, metadata filter 한계 존중   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 2. 쿼리 보강 전략 (확정안 시각화)

```
┌─────────────────────────────────────────────────────────────────┐
│              query 보강 = metadata filter 대체                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Node 1 출력:                                                  │
│   search_query: "머신러닝 입문"                               │
│   target_topics: [머신러닝]                                   │
│   prerequisite_candidates: [선형대수, 확률과통계]             │
│                                                                 │
│              ↓ query_builder가 결합                            │
│                                                                 │
│  보강된 검색 쿼리:                                            │
│   "머신러닝 입문 머신러닝 선형대수 확률과통계"                │
│   (search_query + target name + prerequisite name)            │
│                                                                 │
│  → topic_names 메타데이터(인덱싱됨)와 자연스럽게 벡터 매칭    │
│  → where 필터 없이 의미 검색으로 topic 반영 ✅                │
│                                                                 │
│  필터는 difficulty만 (resources):                             │
│   resource_filter = {"difficulty_level": "beginner"}          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```
---

## 4. 코드 생성 프롬프트

```markdown
# 코드 생성 요청: Node 2 (검색) 구현

## 역할
당신은 LangGraph 기반 AI Agent를 구축하는 시니어 백엔드 엔지니어입니다.
간결하고 실용적인 코드를 작성합니다. 과도한 추상화는 피합니다.

## 프로젝트 컨텍스트
- 프로젝트명: WhereToGo (교육 컨설턴트 AI)
- 현재 단계: LangGraph 단일 Agent의 두 번째 노드 "검색" 구현
- 전체 흐름: [Node1 입력분석] → [Node2 검색] → [Node3 커리큘럼생성]
- 완료: RAG 검색 모듈(ai/search/searcher.py), Node1(입력분석)
- 데이터 범위: 컴퓨터공학 분야 한정 (MVP)

## 핵심 원칙 (반드시 준수)
1. 검색 로직을 새로 만들지 않는다. 기존 searcher를 재사용한다.
   → Node 2는 "어댑터": Node1 출력 → searcher 호출 → Node3 입력 가공
2. Chroma metadata 필터의 한계를 억지로 뚫지 않는다.
   → topic은 metadata filter가 아닌 "query 키워드 보강"으로 반영
3. MVP는 단일 검색 (다중/선수지식 분리 검색은 추후)
4. TypedDict 금지(내부 dict), 오버엔지니어링 금지

## 기존 코드 (재사용)
```python
# ai/search/searcher.py
search(
    query: str,
    n_courses: int = 5,
    n_resources: int = 5,
    course_filter: dict | None = None,    # ChromaDB where
    resource_filter: dict | None = None,
) -> dict
# 반환: {"courses": [...], "resources": [...]}
# 각 결과 dict: {"id", "score", "document", "metadata"}
# metadata에 source_row_number(course), external_id(resource),
#            topic_names 등이 포함되어 있음
```

## Node 1 출력 (Node 2 입력)
```python
{
    "user_profile": {
        "goal": str,
        "difficulty_level": str,   # beginner/intermediate/advanced
        ...
    },
    "topic_analysis": {
        "target_topics": [{"slug","name","depth",...}],
        "prerequisite_candidates": [{"slug","name","reason"}],
        ...
    },
    "search_query": str,
    "is_in_scope": bool
}
```

## 신규 구현 구조
```
ai/agent/nodes/search/
├── __init__.py
├── query_builder.py    # Node1 출력 → 검색 쿼리/필터 구성
└── node.py             # searcher 호출 + 결과 가공
```

## 구현 요구사항

### 1. query_builder.py
검색 쿼리와 필터를 구성 (LLM 불필요, 규칙 기반):

- build_search_query(search_query, topic_analysis) -> str
  - 기반: search_query
  - 보강: target_topics의 name + prerequisite_candidates의 name 결합
  - 예: "머신러닝 입문" + "머신러닝" + "선형대수 확률과통계"
    → "머신러닝 입문 머신러닝 선형대수 확률과통계"
  - 중복 단어 정리(선택)

- build_resource_filter(user_profile) -> dict | None
  - difficulty_level 기반 resource_filter 생성
  - 예: {"difficulty_level": "beginner"}
  - difficulty가 unknown/없음이면 None (필터 미적용)

- (courses는 무필터: course_filter는 항상 None)

### 2. node.py (오케스트레이션)
전체 흐름:
1. is_in_scope 확인 → false면 빈 결과 반환 (검색 스킵)
2. query_builder로 보강 쿼리 + resource_filter 구성
3. searcher.search() 호출 (n_courses=5, n_resources=8)
4. 결과를 Node3 친화적 형식으로 가공
   - course 결과: metadata에서 source_row_number 명시 노출
   - resource 결과: metadata에서 external_id 명시 노출
   - score, name/title 포함
5. State 형식으로 반환

함수: run_search(state: dict) -> dict
- state에서 search_query, topic_analysis, user_profile, is_in_scope 읽음
- 반환: State에 병합될 dict

### 3. 출력 형식 (State 병합용)
```python
{
    "search_results": {
        "courses": [
            {
                "source_row_number": int,   # Node3 FK 매칭 (CurriculumCourse)
                "course_name": str,
                "score": float,
                "metadata": dict             # topic_names 등 포함
            }
        ],
        "resources": [
            {
                "external_id": str,          # Node3 FK 매칭 (LearningResource.lookup_key)
                "title": str,
                "score": float,
                "metadata": dict
            }
        ]
    }
}
```

### 4. 범위 밖(is_in_scope=false) 처리
- 검색 스킵, search_results를 빈 구조로 반환:
  {"search_results": {"courses": [], "resources": []}}
- 로깅으로 스킵 사유 남김
- (흐름 중단은 추후 StateGraph 조건부 엣지에서 처리)

### 5. 식별자 추출 주의
- searcher 결과 metadata에서 source_row_number, external_id 추출
- 키가 없을 경우 방어 처리 (로깅 + 해당 항목 스킵 또는 None)
- 이 식별자는 Node3가 Django 객체(CurriculumCourse, LearningResource)를
  조회하는 데 사용됨

## 코드 품질
- 타입 힌트 (TypedDict 금지, dict 표기)
- 간단명료한 docstring (한국어)
- 필수 예외 처리 (검색 실패, 빈 결과, 식별자 누락)
- logging (보강 쿼리, 결과 건수, 스킵 사유)

## 검증 스크립트
샘플 Node1 출력으로 run_search 실행:
1. 정상: 머신러닝 입력 (target+prerequisite 보강 쿼리 확인)
2. difficulty 필터: beginner → resources 필터 적용 확인
3. 범위 밖: is_in_scope=false → 빈 결과 확인

각 결과의 보강 쿼리 + courses/resources 식별자/score 출력

## 출력 형식
1. 각 파일 전체 코드 (파일명 명시)
2. 검증 스크립트
3. 실행 방법 및 예상 출력

## ⭐ 파일별 역할 설명 (필수)
코드 생성 완료 후 반드시 포함:
- query_builder / node 각 파일 역할
- 기존 searcher와의 연동 방식 (재사용 지점)
- Node1 출력이 어떻게 검색 쿼리로 변환되는지
- Node3에서 source_row_number/external_id로 Django 객체를
  어떻게 조회하게 되는지

## 기타
- 한국어 주석/docstring
- 이 단계는 "검색 연결"에만 집중 (커리큘럼 생성 제외)
```

---

## 5. 검토 포인트

```
┌─────────────────────────────────────────────────────────────────┐
│              생성 코드 검토 체크리스트                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✓ 기존 searcher를 재사용하는가? (재구현 X)                  │
│  ✓ topic이 metadata filter가 아닌 query 보강으로 반영?       │
│  ✓ resources만 difficulty 필터, courses 무필터인가?          │
│  ✓ source_row_number / external_id가 결과에 노출되는가?      │
│  ✓ is_in_scope=false 시 검색 스킵 + 빈 결과인가?             │
│  ✓ courses=5, resources=8 적용되는가?                        │
│  ✓ 식별자 누락 방어 처리가 있는가?                           │
│  ✓ TypedDict 없이 dict인가?                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```
---
