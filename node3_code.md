# Node 3 (커리큘럼 생성) 의사결정 확정 + 코드 생성 프롬프트

모든 결정이 명확하고, Node 1~2의 "AI는 식별자만, FK는 백엔드" 원칙이 일관되게 유지되었습니다. 확정 사항을 정리하고 프롬프트를 제작합니다.

---

## 1. 확정 사항 요약

```
┌─────────────────────────────────────────────────────────────────┐
│              Node 3 의사결정 확정                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  N3-1 책임경계 : AI는 순수 JSON(식별자만), FK는 백엔드        │
│  N3-2 출력스키마: title/difficulty/reason/steps[] 확정        │
│  N3-3 배치방식 : LLM 배치 + 후처리 식별자 검증(제거)          │
│  N3-4 단계수   : target_weeks 기준 구간별                     │
│  N3-5 topic    : step당 1개 / fallback "computer-science"     │
│  N3-6 시간배분 : 총합 ≈ target_weeks × weekly_hours           │
│  N3-7 빈결과   : scope=false 또는 빈 검색 → 스킵+안내         │
│                                                                 │
│  핵심: ORM 미접근, 식별자 검증으로 환각 차단                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 2. 환각 차단 검증 흐름 (N3-3 핵심)

```
┌─────────────────────────────────────────────────────────────────┐
│              LLM 식별자 환각 후처리 검증                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Node2 search_results에 존재하는 식별자 집합:                 │
│   valid_courses = {537, 711, ...}                            │
│   valid_resources = {"KOCW_123", "KMOOC_45", ...}            │
│                                                               │
│              ↓ LLM 생성 후                                    │
│                                                               │
│  각 step의 식별자 검증:                                       │
│   course_source_row_numbers ∩ valid_courses                  │
│   resource_external_ids ∩ valid_resources                    │
│                                                               │
│  → 검색결과에 없는 식별자(환각)는 제거                       │
│  → 백엔드가 .get() 실패 없이 안전하게 FK 조회 가능           │
│                                                               │
└─────────────────────────────────────────────────────────────────┘
```

## 3. target_topic_slug 검증 흐름 (N3-5)

```
┌─────────────────────────────────────────────────────────────────┐
│              target_topic_slug 검증                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  유효 slug 집합 (Node1에서):                                  │
│   target_topics + context_topics + prerequisite_candidates    │
│   의 slug들                                                   │
│                                                               │
│  각 step의 target_topic_slug 검증:                            │
│   - 유효 집합에 있으면 → 그대로                              │
│   - 없으면(환각) → fallback "computer-science"               │
│                                                               │
│  → 백엔드가 slug→Topic 조회, 없으면 SET_NULL                │
│                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 코드 생성 프롬프트

```markdown
# 코드 생성 요청: Node 3 (커리큘럼 생성) 구현

## 역할
당신은 LangGraph 기반 AI Agent를 구축하는 시니어 백엔드 엔지니어입니다.
간결하고 실용적인 코드를 작성합니다. 과도한 추상화는 피합니다.

## 프로젝트 컨텍스트
- 프로젝트명: WhereToGo (교육 컨설턴트 AI)
- 현재 단계: LangGraph 단일 Agent의 세 번째 노드 "커리큘럼 생성"
- 전체 흐름: [Node1 입력분석] → [Node2 검색] → [Node3 커리큘럼생성]
- 완료: Node1(입력분석), Node2(검색)
- 데이터 범위: 컴퓨터공학 분야 한정 (MVP)

## 핵심 원칙 (반드시 준수)
1. Node 3는 Django ORM에 직접 접근하지 않는다.
   LLM은 저장 가능한 순수 JSON만 생성한다. (Node1~2와 일관)
2. AI는 식별자만 반환. FK 매핑/저장은 Django 백엔드 책임.
3. LLM은 search_results에 존재하는 식별자만 사용.
   후처리에서 존재하지 않는 식별자는 제거한다 (환각 차단).
4. TypedDict 금지(내부 dict), 오버엔지니어링 금지.
5. LLM 출력은 JSON 강제 + 파싱 실패 방어.

## 기술 스택
- GMS 프록시 OpenAI 호환 LLM (config에서 로드)
- base_url: https://gms.ssafy.io/gmsapi/api.openai.com/v1

## 입력 (State)

### Node1 출력
```python
{
    "user_profile": {
        "goal": str,
        "purpose": str,
        "difficulty_level": str,       # beginner/intermediate/advanced
        "target_weeks": int,
        "weekly_available_hours": int,
        "preferred_learning_style": str
    },
    "topic_analysis": {
        "target_topics": [{"slug","name","depth",...}],
        "context_topics": [{"slug","name",...}],
        "prerequisite_candidates": [{"slug","name",...}],
        ...
    },
    "is_in_scope": bool
}
```

### Node2 출력
```python
{
    "search_results": {
        "courses": [
            {"source_row_number": int, "course_name": str,
             "score": float, "metadata": dict}
        ],
        "resources": [
            {"external_id": str, "title": str,
             "score": float, "metadata": dict}
        ]
    }
}
```

## 신규 구현 구조
```
ai/agent/nodes/curriculum/
├── __init__.py
├── prompt_builder.py    # LLM 프롬프트 구성
├── llm_generator.py     # LLM 호출 + JSON 파싱
├── validator.py         # 식별자/slug 후처리 검증
└── node.py              # 오케스트레이션
```

## 출력 스키마 (LLM 생성 → 백엔드 저장용)
```python
{
    "title": str,                    # 커리큘럼명 (LLM 생성)
    "difficulty_level": str,         # beginner/intermediate/advanced
    "recommendation_reason": str,    # 추천 근거 (LLM 생성)
    "steps": [
        {
            "step_order": int,
            "title": str,
            "description": str,
            "target_topic_slug": str,          # step당 1개
            "difficulty_level": str,
            "estimated_hours": int,
            "prerequisite_note": str,
            "course_source_row_numbers": [int],   # Node2 식별자
            "resource_external_ids": [str]        # Node2 식별자
        }
    ]
}
```
※ goal/target_weeks/weekly_available_hours/preferred_learning_style은
  Node1 user_profile에서 백엔드가 직접 가져가므로 이 출력에 미포함
  (단, 백엔드 저장 편의를 위해 node.py 최종 반환 시 user_profile도 함께 전달)

## 구현 요구사항

### 1. prompt_builder.py
LLM 프롬프트 구성 (규칙 기반):
- build_curriculum_prompt(user_profile, topic_analysis, search_results) -> str(or messages)
- 프롬프트에 포함할 정보:
  - 학습 목표, 난이도, 목표 기간, 주간 시간, 선호 학습 방식
  - target/context/prerequisite topics (slug + name)
  - 검색된 courses 목록 (source_row_number + course_name)
  - 검색된 resources 목록 (external_id + title)
- 프롬프트 지시사항:
  - search_results에 있는 식별자만 사용하라고 명시
  - 단계 수 가이드 (target_weeks 기준, 아래 규칙)
  - 총 estimated_hours ≈ target_weeks × weekly_available_hours
  - target_topic_slug는 제공된 topic slug 중에서 선택
  - JSON 형식으로만 응답

#### 단계 수 가이드
- 4주 이하: 3~4단계
- 8주 이하: 4~5단계
- 16주 이하: 5~7단계
- 16주 초과: 6~8단계

### 2. llm_generator.py
- GMS 프록시 OpenAI 호환 클라이언트 사용 (config 로드)
- 프롬프트 전달 → JSON 응답 파싱
- JSON 파싱 실패 시 방어 (로깅 + 안전한 에러 반환)
- 함수: generate_curriculum(prompt) -> dict

### 3. validator.py (환각 차단 핵심)
LLM 출력 후처리 검증:

- validate_identifiers(curriculum, search_results) -> dict
  - search_results에서 유효 식별자 집합 추출:
    valid_courses = {course의 source_row_number}
    valid_resources = {resource의 external_id}
  - 각 step의 course_source_row_numbers를 valid_courses와 교집합
  - 각 step의 resource_external_ids를 valid_resources와 교집합
  - 존재하지 않는 식별자는 제거

- validate_topic_slugs(curriculum, topic_analysis) -> dict
  - 유효 slug 집합: target+context+prerequisite의 slug
  - 각 step의 target_topic_slug 검증
  - 유효 집합에 없으면 "computer-science" fallback

- (선택) step_order 정합 보정 (1부터 순차)

### 4. node.py (오케스트레이션)
전체 흐름:
1. 스킵 조건 확인:
   - is_in_scope=false 또는
   - courses와 resources가 모두 비어있음
   → 커리큘럼 생성 스킵, 안내 메시지 반환:
     {"curriculum": None,
      "message": "커리큘럼 생성에 필요한 정보가 부족합니다..."}
2. prompt_builder로 프롬프트 구성
3. llm_generator로 커리큘럼 JSON 생성
4. validator로 식별자/slug 후처리 검증
5. State 형식 반환

함수: run_curriculum_generation(state: dict) -> dict
반환: State에 병합될 dict
```python
{
    "curriculum": {
        "title": str,
        "difficulty_level": str,
        "recommendation_reason": str,
        "steps": [...]
    }
    # (백엔드 저장 편의를 위해 user_profile은 State에 이미 존재하므로
    #  curriculum에 중복 포함하지 않음. node 반환은 curriculum 키만)
}
```

## 코드 품질
- 타입 힌트 (TypedDict 금지, dict 표기)
- 간단명료한 docstring (한국어)
- 필수 예외 처리 (LLM 실패, JSON 파싱 실패, 빈 입력)
- logging (스킵 사유, 생성 단계 수, 제거된 환각 식별자 수)

## 검증 스크립트
fake LLM 응답(또는 실제 호출) 기반 테스트:
1. 정상: 머신러닝 입력 + 검색결과 → 커리큘럼 생성
   - 단계 수가 target_weeks 가이드에 맞는지
   - estimated_hours 합이 가용시간에 근접하는지
2. 환각 검증: LLM이 없는 식별자 인용 → 제거 확인
3. slug fallback: 유효하지 않은 slug → "computer-science" 확인
4. 스킵: is_in_scope=false 또는 빈 검색결과 → 안내 메시지

## 출력 형식
1. 각 파일 전체 코드 (파일명 명시)
2. 검증 스크립트 (fake search_results/LLM 응답 포함)
3. 실행 방법 및 예상 출력

## ⭐ 파일별 역할 설명 (필수)
코드 생성 완료 후 반드시 포함:
- prompt_builder/llm_generator/validator/node 각 역할
- Node1(user_profile/topic_analysis), Node2(search_results)가
  어떻게 입력으로 활용되는지
- 출력 JSON이 Django 모델(Curriculum, CurriculumStep,
  CurriculumStepCourse, CurriculumStepResource)에 어떻게
  매핑되는지 (백엔드가 식별자로 FK 조회)
- validator가 환각을 차단하는 방식

## 기타
- 한국어 주석/docstring
- 이 단계는 "커리큘럼 생성"에만 집중 (저장/StateGraph 통합 제외)
```

---

## 5. 검토 포인트

```
┌─────────────────────────────────────────────────────────────────┐
│              생성 코드 검토 체크리스트                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✓ ORM 미접근 / 순수 JSON 출력인가?                          │
│  ✓ 식별자 환각 검증(교집합 제거)이 작동하는가?               │
│  ✓ slug fallback("computer-science")이 적용되는가?           │
│  ✓ 단계 수가 target_weeks 가이드를 따르는가?                 │
│  ✓ estimated_hours 합이 가용시간에 근접하는가?               │
│  ✓ scope=false/빈결과 시 스킵+안내인가?                      │
│  ✓ 출력 스키마가 Django 모델 매핑 가능한가?                  │
│  ✓ LLM JSON 파싱 실패 방어가 있는가?                         │
│  ✓ TypedDict 없이 dict인가?                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 6. 진행 상황

```
┌─────────────────────────────────────────────────────────────────┐
│              LangGraph Agent 구축 진행                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Node 1 입력 분석    ✅ 구현 완료                            │
│  Node 2 검색         ✅ 구현 완료 (fake search 검증)         │
│  Node 3 커리큘럼생성 🔨 설계완료 → 코드 생성 단계            │
│  StateGraph 통합     ⬜ 대기 (3노드 완성 후 다음 단계!)      │
│                                                                 │
│  [남은 백엔드 확인] lookup_key == external_id 저장 확인       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---
