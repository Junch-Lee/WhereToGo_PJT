# WhereToGo - 교육 컨설턴트 AI

WhereToGo는 개인 학습자의 목표, 현재 수준, 학습 가능 시간, 선호 학습 방식을 바탕으로 실제 강의/학습 자료 데이터를 검색하고, 생성형 AI를 활용해 개인 맞춤 커리큘럼을 추천하는 서비스입니다.

- 프로젝트 기간: 2026.05.08 ~ 2026.06.25
- 주요 대상: 개인 학습자
- 핵심 목표: 실제 보유한 강의/학습 자료를 근거로 신뢰 가능한 개인 맞춤 학습 로드맵 제공

## 목차

- [A. 팀원 정보 및 업무 분담 내역](#a-팀원-정보-및-업무-분담-내역)
- [B. 목표 서비스 및 실제 구현 정도](#b-목표-서비스-및-실제-구현-정도)
- [C. 데이터베이스 모델링 ERD](#c-데이터베이스-모델링-erd)
- [D. 추천 알고리즘에 대한 기술적 설명](#d-추천-알고리즘에-대한-기술적-설명)
- [E. 핵심 기능에 대한 설명](#e-핵심-기능에-대한-설명)
- [F. 생성형 AI를 활용한 부분](#f-생성형-ai를-활용한-부분)
- [G. 서비스 URL](#g-서비스-url)
- [H. 기타 포함 내용](#h-기타-포함-내용)

## A. 팀원 정보 및 업무 분담 내역

### 팀 정보

| 구분 | 내용 |
| --- | --- |
| 프로젝트명 | WhereToGo - 교육 컨설턴트 AI |
| 과정 | SSAFY 15기 1학기 관통 프로젝트 |
| 팀 | 서울 1반 Python 프로젝트 |
| Git 이력에서 확인되는 기여 계정 | `ChangJun_Lee`, `ChangJun-Lee`, `Junch-Lee`, `WinterI5Coming` |

### 업무 분담

아래 분담은 현재 구현된 코드 영역을 기준으로 정리했습니다. 제출 전 실제 팀원 이름을 최종 명단에 맞게 보정하면 됩니다.

| 담당 영역 | 주요 업무 | 관련 코드/산출물 |
| --- | --- | --- |
| 프로젝트 기획/서비스 설계 | 개인 학습자 대상 AI 교육 컨설턴트 서비스 정의, 커리큘럼 생성 플로우 설계, 기술 의사결정 문서화 | Notion 기술적 의사결정 문서, `README.md` |
| 데이터 수집/전처리 | KOCW/K-MOOC 학습 자료 수집, 대학 강의계획서 데이터 정제, topic 후보 추출 및 검토 데이터 생성 | `curriculum-data/`, `scripts/topic_pipeline/`, `ai/data/` |
| ERD/DB 모델링 | 사용자, topic, 강의/자료, 커리큘럼, 학습 진행 모델 설계 및 migration 작성 | `apps/accounts/models.py`, `apps/curriculum/models.py` |
| 백엔드 API | 인증, 사용자 프로필, topic, 커리큘럼 생성/저장/진행, 학습 대시보드 API 구현 | `apps/accounts/`, `apps/curriculum/views.py`, `apps/curriculum/services/` |
| AI/RAG/Agent | ChromaDB 인덱싱, embedding 설정, LangGraph 기반 Agent, 검색 결과 기반 커리큘럼 생성 및 검증 | `ai/core/`, `ai/indexing/`, `ai/search/`, `ai/agent/` |
| 프론트엔드 | Vue 기반 랜딩/로그인/마이페이지/인터뷰/커리큘럼 결과/상세/학습 대시보드 화면 구현 | `frontend/src/pages/`, `frontend/src/api/`, `frontend/src/components/` |
| 테스트/검증 | serializer, curriculum API, 학습 진행 API, 학습 대시보드 API 테스트 작성 | `apps/curriculum/tests.py`, `apps/curriculum/test_curriculum_learning_api.py`, `apps/curriculum/test_learning_dashboard_api.py` |

## B. 목표 서비스 및 실제 구현 정도

### 목표 서비스

WhereToGo의 목표는 “사용자의 현재 상황을 이해하고, 실제 학습 데이터에 기반한 개인 맞춤 커리큘럼을 추천하며, 이후 학습 진행까지 관리하는 교육 컨설턴트 AI”입니다.

초기 목표는 다음과 같았습니다.

- 사용자의 학습 목표와 수준을 입력받는다.
- 보유한 강의/학습 자료 데이터에서 적합한 자료를 찾는다.
- AI가 학습 순서, 추천 이유, 단계별 강의/자료를 포함한 커리큘럼을 생성한다.
- 사용자는 생성 결과를 확인한 뒤 저장한다.
- 저장한 커리큘럼을 기반으로 학습을 시작, 일시정지, 재개, 완료할 수 있다.
- 학습 대시보드에서 현재 진행 상황과 다음 학습 항목을 확인한다.

### 실제 구현 정도

| 기능 | 구현 상태 | 설명 |
| --- | --- | --- |
| 회원가입/로그인 | 구현 완료 | JWT 기반 인증, 사용자 정보 조회/수정 API 구현 |
| 사용자 학습 프로필 | 구현 완료 | 주간 학습 가능 시간, 선호 학습 방식 등 저장 |
| topic 체계 | 구현 완료 | 최대 3-depth topic, topic alias, 관심 topic 모델 구현 |
| 강의/학습 자료 데이터 | 구현 완료 | 대학 강의계획서와 KOCW/K-MOOC 자료 모델링 |
| topic-data 연결 | 구현 완료 | `CourseTopic`, `ResourceTopic`으로 강의/자료와 topic 연결 |
| RAG 검색 | 구현 완료 | ChromaDB `courses`, `resources` collection 기반 검색 |
| AI Agent | 구현 완료 | 입력 분석 -> 검색 -> 커리큘럼 생성 흐름 구현 |
| 커리큘럼 생성 API | 구현 완료 | 일반 생성 API와 streaming 생성 API 제공 |
| 생성 결과 미리보기 | 구현 완료 | AI 결과를 DB 저장 전 preview 형태로 반환 |
| 생성 결과 저장 | 구현 완료 | 사용자가 저장을 선택하면 curriculum/step/recommendation 저장 |
| 학습 시작/진행 | 구현 완료 | step progress, schedule, learning progress 생성 및 상태 변경 |
| 학습 대시보드 API | 구현 완료 | 요약, 현재 학습, 커리큘럼별 진행률, 로드맵 API 구현 |
| 프론트엔드 화면 | 구현 완료 | Vue 기반 주요 사용자 화면 구현 |
| 배포 | 미배포 | 현재 로컬 실행 기준 프로젝트 |

### 프로젝트 구조

실제 구현 구조는 백엔드가 별도 `backend/` 폴더에 있지 않고, Django 프로젝트가 루트에 위치합니다.

```text
WhereToGo_PJT/
├─ manage.py
├─ requirements.txt
├─ config/
│  ├─ settings.py
│  └─ urls.py
├─ apps/
│  ├─ accounts/
│  └─ curriculum/
├─ ai/
│  ├─ agent/
│  ├─ core/
│  ├─ indexing/
│  └─ search/
├─ scripts/topic_pipeline/
├─ curriculum-data/
└─ frontend/
   ├─ src/
   └─ package.json
```

### 기술 스택

| 영역 | 기술 |
| --- | --- |
| Backend | Python, Django 5.2, Django REST Framework, Simple JWT, drf-spectacular |
| Database | SQLite |
| AI/RAG | OpenAI, LangGraph, ChromaDB, `text-embedding-3-small`, `gpt-4o-mini` |
| Data | pandas, CSV pipeline |
| Frontend | Vue 3, Vue Router, Vite, Axios |

## C. 데이터베이스 모델링 ERD

첨부 ERD 초안에는 인터뷰, 진단, 학습 노트 등 확장 엔티티가 포함되어 있었지만, 현재 실제 구현 기준 ERD는 아래 엔티티를 중심으로 정리하는 것이 정확합니다.

### Accounts

| 테이블 | 모델 | 역할 |
| --- | --- | --- |
| `users` | `User` | 이메일 기반 커스텀 사용자 |
| `user_profiles` | `UserProfile` | 주간 학습 가능 시간, 선호 학습 방식 등 사용자 학습 프로필 |
| `user_interest_topics` | `UserInterestTopic` | 사용자가 관심 있는 학습 주제 |
| `topics` | `Topic` | 학습 개념 단위. parent 구조로 최대 3-depth 주제 체계 표현 |
| `topic_aliases` | `TopicAlias` | 동일 topic에 대한 한글/영문/별칭 매핑 |

### Curriculum / Resource

| 테이블 | 모델 | 역할 |
| --- | --- | --- |
| `categories` | `Category` | 커리큘럼 표시/관리용 분야 분류 |
| `learning_resources` | `LearningResource` | KOCW/K-MOOC 등 온라인 학습 자료 |
| `curriculum_courses` | `CurriculumCourse` | 대학 강의계획서 기반 강의 데이터 |
| `resource_topics` | `ResourceTopic` | 학습 자료와 topic 연결 |
| `course_topics` | `CourseTopic` | 대학 강의와 topic 연결 |
| `curricula` | `Curriculum` | 사용자별 커리큘럼 |
| `curriculum_categories` | `CurriculumCategory` | 커리큘럼과 category 연결 |
| `curriculum_steps` | `CurriculumStep` | AI가 생성한 커리큘럼 단계 |
| `curriculum_step_resources` | `CurriculumStepResource` | step별 추천 학습 자료 |
| `curriculum_step_courses` | `CurriculumStepCourse` | step별 추천 대학 강의 |
| `curriculum_step_progresses` | `CurriculumStepProgress` | 사용자별 step 진행 상태 |
| `learning_schedules` | `LearningSchedule` | 현재 또는 예정 학습 일정 |
| `learning_progresses` | `LearningProgress` | 실제 학습 기록 |

### 관계 요약

- `User` 1:N `Curriculum`
- `User` 1:1 `UserProfile`
- `Topic` self-relation으로 대분류/중분류/소분류 구조 구성
- `Topic` 1:N `TopicAlias`
- `CurriculumCourse` N:M `Topic` through `CourseTopic`
- `LearningResource` N:M `Topic` through `ResourceTopic`
- `Curriculum` 1:N `CurriculumStep`
- `CurriculumStep` N:M `CurriculumCourse` through `CurriculumStepCourse`
- `CurriculumStep` N:M `LearningResource` through `CurriculumStepResource`
- `CurriculumStep` 1:N `CurriculumStepProgress`
- `CurriculumStepProgress` 1:N `LearningSchedule`
- `LearningSchedule` 1:N `LearningProgress`

### 모델링 의사결정

핵심 추천 로직은 category가 아니라 topic 중심으로 설계했습니다. Category는 관리와 표시를 돕는 보조 분류로 유지하고, 실제 검색과 추천 연결은 `topics`, `course_topics`, `resource_topics`를 중심으로 수행합니다.

이유는 다음과 같습니다.

- category는 “컴퓨터/인공지능/데이터”처럼 넓은 분야를 표현하기 쉽지만, 실제 추천에는 “선형 회귀”, “REST API”, “데이터 전처리” 같은 세부 학습 개념이 필요합니다.
- 같은 개념이 한글/영문/약어로 표현될 수 있어 `TopicAlias`로 표준 topic에 연결해야 합니다.
- 강의와 학습 자료를 같은 topic 기준으로 연결하면 서로 다른 출처의 데이터를 함께 추천할 수 있습니다.

현재 구현에서 제외된 확장 항목:

- `interview_sessions`
- `interview_messages`
- `diagnostic_questions`
- `diagnostic_attempts`
- `diagnostic_answers`
- `learning_notes`
- `user_skill_profiles`

## D. 추천 알고리즘에 대한 기술적 설명

### 전체 추천 흐름

WhereToGo의 추천은 단순 키워드 검색이나 순수 LLM 생성이 아니라, RAG + Agent 구조로 동작합니다.

```text
사용자 입력
  -> 입력 검증 및 raw_input 변환
  -> Topic catalog 기반 입력 분석
  -> courses/resources vector search
  -> 검색 결과를 근거로 커리큘럼 생성
  -> 생성 결과 identifier 검증
  -> preview 반환
  -> 사용자 저장 시 DB 반영
```

구현 위치:

- `apps/curriculum/serializers.py`
- `apps/curriculum/views.py`
- `ai/agent/graph.py`
- `ai/search/searcher.py`
- `ai/agent/nodes/curriculum/03_validator.py`

### 입력 검증 및 Agent 입력 변환

프론트엔드 입력값을 그대로 AI에 전달하지 않고, serializer에서 검증한 뒤 Agent가 기대하는 key로 변환합니다.

```python
class CurriculumGenerateSerializer(serializers.Serializer):
    goal = serializers.CharField(required=True, allow_blank=False)
    purpose = serializers.ChoiceField(required=True, choices=PURPOSE_CHOICES)
    difficulty_level = serializers.ChoiceField(required=True, choices=DIFFICULTY_LEVEL_CHOICES)
    target_weeks = serializers.ChoiceField(required=True, choices=TARGET_WEEKS_CHOICES)
    weekly_available_hours = serializers.ChoiceField(required=True, choices=WEEKLY_AVAILABLE_HOURS_CHOICES)
    preferred_learning_style = serializers.ChoiceField(required=True, choices=PREFERRED_LEARNING_STYLE_CHOICES)

    def to_raw_input(self) -> dict:
        data = self.validated_data
        return {
            "goal_text": data["goal"],
            "purpose": data["purpose"],
            "level": data["difficulty_level"],
            "period": data["target_weeks"],
            "weekly_hours": data["weekly_available_hours"],
            "learning_style": data["preferred_learning_style"],
            "concern": "",
        }
```

### RAG 검색

ChromaDB에는 강의 데이터와 학습 자료 데이터를 별도 collection으로 저장합니다.

- `courses`: 대학 강의계획서 기반 강의 데이터
- `resources`: KOCW/K-MOOC 등 온라인 학습 자료

AI 설정은 `ai/core/config.py`에서 관리합니다.

```python
DEFAULT_CHROMA_PERSIST_DIR = "./rag/data/chroma_db"
DEFAULT_COLLECTION_COURSES = "courses"
DEFAULT_COLLECTION_RESOURCES = "resources"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
```

문서 단위 인덱싱을 선택한 이유:

- 학습 자료와 강의계획서 row의 길이가 embedding 모델 입력 한도보다 작았습니다.
- 하나의 강의/자료 row가 추천 단위와 일치했습니다.
- chunking을 적용하면 검색 결과를 다시 강의/자료 단위로 묶는 후처리가 필요했습니다.

### Agent 실행

LangGraph 기반 Agent는 입력 분석, 검색, 커리큘럼 생성을 단계적으로 실행합니다.

```python
def run_agent(raw_input: dict, catalog: list[dict]) -> dict[str, Any]:
    graph = build_agent_graph(catalog)
    result = graph.invoke({"raw_input": raw_input})
    return dict(result)
```

### 검색 결과 기반 생성 검증

LLM이 실제 검색 결과에 없는 강의나 자료를 만들어내는 문제를 막기 위해, 생성 후 identifier를 검증합니다.

```python
def validate_identifiers(curriculum: dict, search_results: dict) -> dict:
    valid_courses = {
        _to_int(course.get("source_row_number"))
        for course in search_results.get("courses", [])
        if _to_int(course.get("source_row_number")) is not None
    }
    valid_resources = {
        _clean_text(resource.get("external_id"))
        for resource in search_results.get("resources", [])
        if _clean_text(resource.get("external_id"))
    }

    for step in curriculum.get("steps", []):
        step["course_source_row_numbers"] = [
            value for value in step.get("course_source_row_numbers", [])
            if _to_int(value) in valid_courses
        ]
        step["resource_external_ids"] = [
            value for value in step.get("resource_external_ids", [])
            if _clean_text(value) in valid_resources
        ]

    return curriculum
```

### 추천 알고리즘 의사결정

| 방식 | 장점 | 한계 | 최종 판단 |
| --- | --- | --- | --- |
| Rule-based | 동작이 예측 가능함 | 사용자의 다양한 목표와 표현을 반영하기 어려움 | 단독 사용하지 않음 |
| Keyword search | 구현이 간단하고 빠름 | 학습 수준, 기간, 선호 방식 반영이 약함 | RAG 검색의 일부로 활용 |
| Pure LLM | 자연어 생성 품질이 좋음 | 실제 보유 데이터에 없는 강의/자료를 생성할 위험 | 단독 사용하지 않음 |
| RAG + Agent | 실제 데이터 기반성과 개인화 흐름을 함께 확보 | 구조가 복잡하고 검증 로직 필요 | 최종 선택 |

## E. 핵심 기능에 대한 설명

### 1. 회원가입/로그인/사용자 프로필

사용자는 이메일 기반 계정으로 가입하고 JWT로 인증합니다. 이후 마이페이지에서 사용자 정보와 학습 프로필을 관리합니다.

주요 API:

| Method | URL | 설명 |
| --- | --- | --- |
| POST | `/api/auth/signup/` | 회원가입 |
| POST | `/api/auth/login/` | 로그인 |
| POST | `/api/auth/token/refresh/` | JWT refresh |
| GET/PATCH | `/api/users/me/` | 내 정보 조회/수정 |
| GET/PATCH | `/api/users/me/profile/` | 학습 프로필 조회/수정 |

### 2. 커리큘럼 생성

사용자가 입력한 목표와 학습 조건을 기반으로 AI Agent가 커리큘럼 preview를 생성합니다.

주요 API:

| Method | URL | 설명 |
| --- | --- | --- |
| POST | `/api/curriculums/generate/` | AI 커리큘럼 생성 |
| POST | `/api/curriculums/generate/stream/` | 생성 진행 상황 스트리밍 |

스트리밍 API는 생성 중 진행률과 문구를 반환해 사용자에게 대기 상태를 보여줍니다.

```python
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_curriculum_stream(request):
    def event_stream():
        serializer = CurriculumGenerateSerializer(data=request.data)
        if not serializer.is_valid():
            yield _sse_event("error", {"detail": serializer.errors})
            return

        yield _sse_event("progress", {"progress": 10})
        raw_input = serializer.to_raw_input()

        yield _sse_event("progress", {"progress": 25})
        catalog = build_topic_catalog()

        yield _sse_event("progress", {"progress": 45})
        agent_result = run_agent(raw_input, catalog)

        yield _sse_event("progress", {"progress": 80})
        normalized_result = normalize_agent_response(agent_result)
        yield _sse_event("done", normalized_result)

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")
```

### 3. 생성 결과 저장

AI 생성 결과는 곧바로 DB에 저장하지 않고, 먼저 사용자에게 preview로 보여줍니다. 사용자가 저장을 선택하면 curriculum과 step, 추천 강의/자료 연결이 저장됩니다.

```python
@transaction.atomic
def save_ai_generated_curriculum(user, ai_result: dict):
    curriculum = Curriculum.objects.create(...)
    for step_data in steps:
        step = CurriculumStep.objects.create(curriculum=curriculum, ...)
        CurriculumStepCourse.objects.create(curriculum_step=step, ...)
        CurriculumStepResource.objects.create(curriculum_step=step, ...)
    return curriculum
```

주요 API:

| Method | URL | 설명 |
| --- | --- | --- |
| POST | `/api/curriculums/save-generated/` | AI 생성 결과 저장 |
| GET | `/api/curriculums/{id}/` | 커리큘럼 상세 조회 |

### 4. 학습 시작/일시정지/재개/완료

커리큘럼을 저장한 뒤 사용자는 학습을 시작할 수 있습니다. 학습 시작 시 전체 일정을 미리 만들지 않고, 현재 시작하는 step에 대해서만 진행 정보와 일정을 생성합니다.

```python
@transaction.atomic
def start_curriculum_learning(curriculum, user, scheduled_date=None):
    validate_curriculum_owner(curriculum, user)
    curriculum = Curriculum.objects.select_for_update().get(id=curriculum.id)

    next_step = get_next_pending_step(curriculum, user)
    step_progress = _get_or_create_step_progress(curriculum, next_step)
    step_progress.status = CurriculumStepProgress.Status.IN_PROGRESS

    schedule = get_or_create_learning_schedule(step_progress, scheduled_date)
    progress = get_or_create_learning_progress(step_progress, schedule)

    curriculum.status = Curriculum.Status.ACTIVE
    curriculum.current_step = next_step
    curriculum.save(...)
```

주요 API:

| Method | URL | 설명 |
| --- | --- | --- |
| POST | `/api/curriculums/{id}/start/` | 학습 시작 |
| POST | `/api/curriculums/{id}/pause/` | 학습 일시정지 |
| POST | `/api/curriculums/{id}/resume/` | 학습 재개 |
| POST | `/api/curriculums/{id}/complete/` | 커리큘럼 완료 |
| POST | `/api/curriculums/{id}/steps/{step_id}/complete/` | 특정 step 완료 |

### 5. 학습 대시보드

학습 대시보드는 저장된 커리큘럼과 학습 진행 데이터를 기반으로 구성됩니다.

제공 가능한 정보:

- 진행 중인 커리큘럼 수
- 완료한 커리큘럼 수
- 현재 학습 중인 step
- 전체 step 대비 완료 step 비율
- 오늘/이번 주 학습 예정 항목
- step별 추천 강의와 학습 자료
- 커리큘럼 상태별 목록

주요 API:

| Method | URL | 설명 |
| --- | --- | --- |
| GET | `/api/learning/dashboard/` | 학습 대시보드 요약 |
| GET | `/api/learning/curriculums/progress/` | 커리큘럼별 진행률 |
| GET | `/api/learning/current/` | 현재 학습 중인 항목 |
| GET | `/api/learning/roadmap/` | 학습 로드맵 |

### 6. API 문서

| Method | URL | 설명 |
| --- | --- | --- |
| GET | `/api/schema/` | OpenAPI schema |
| GET | `/api/docs/` | Swagger UI |

## F. 생성형 AI를 활용한 부분

### 활용 위치

| 활용 영역 | 설명 | 구현 위치 |
| --- | --- | --- |
| 사용자 입력 분석 | 목표 문장을 topic 후보와 검색 의도로 변환 | `ai/agent/nodes/input_analysis/` |
| RAG 검색 질의 구성 | 사용자 목표와 topic catalog를 바탕으로 검색 query 구성 | `ai/agent/nodes/search/` |
| 커리큘럼 생성 | 검색된 강의/자료를 근거로 step별 학습 계획 생성 | `ai/agent/nodes/curriculum/` |
| 추천 이유 생성 | 왜 해당 step과 자료가 필요한지 자연어 설명 생성 | `ai/agent/nodes/curriculum/01_prompt_builder.py` |
| 생성 결과 정규화 | AI 응답을 백엔드 응답/저장 가능한 구조로 변환 | `apps/curriculum/services/agent_response_service.py` |

### 사용 모델

- Chat model: `gpt-4o-mini`
- Embedding model: `text-embedding-3-small`
- Vector DB: ChromaDB

### 생성형 AI 사용 시 고려한 점

#### 1. 실제 데이터 기반성

AI가 없는 강의나 자료를 임의로 만들어내지 않도록, prompt에서 검색 결과에 포함된 course/resource identifier만 사용하도록 제한했습니다. 이후 validator에서 한 번 더 검증합니다.

#### 2. Preview와 Save 분리

AI 생성 결과를 바로 DB에 저장하면 잘못된 결과가 사용자 데이터로 남을 수 있습니다. 따라서 생성 결과는 preview로 먼저 보여주고, 사용자가 저장을 선택한 뒤 DB에 반영합니다.

#### 3. Topic 체계 보호

LLM이 추출한 topic 후보를 곧바로 `topics`에 저장하지 않았습니다. topic은 추천 품질의 기준점이므로 seed topic, alias, matching, review pipeline을 거쳐 관리합니다.

#### 4. 긴 처리 시간에 대한 UX

AI 호출과 vector search가 포함되므로 응답이 느릴 수 있습니다. `StreamingHttpResponse`를 적용해 진행률과 문구를 지속적으로 갱신하도록 했습니다.

## G. 서비스 URL

현재 프로젝트는 배포 서버 없이 로컬 실행 기준으로 구성되어 있습니다.

| 구분 | URL |
| --- | --- |
| Backend local | `http://localhost:8000` |
| Frontend local | `http://localhost:5173` |
| Swagger local | `http://localhost:8000/api/docs/` |
| 배포 URL | 미배포 |

### Backend 실행

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### AI 환경 변수

AI 설정은 `ai/core/config.py`에서 `ai/.env`와 프로세스 환경 변수를 읽습니다.

```env
GMS_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_CHAT_MODEL=gpt-4o-mini
CHROMA_PERSIST_DIR=./rag/data/chroma_db
COLLECTION_COURSES=courses
COLLECTION_RESOURCES=resources
EMBEDDING_MODEL=text-embedding-3-small
```

### 데이터 적재

```bash
python manage.py import_topic_pipeline_data
```

필요하면 topic 연결 정보만 초기화한 뒤 다시 적재할 수 있습니다.

```bash
python manage.py import_topic_pipeline_data --clear-topic-links
```

### ChromaDB 인덱싱

```bash
python -m ai.indexing.index_embeddings --target all --reset
```

### Frontend 실행

```bash
cd frontend
npm install
npm run dev
```

## H. 기타 포함 내용

### 기술적 의사결정 요약

#### Topic 중심 모델링

초기에는 category 중심 분류를 고려했지만, 실제 추천에는 더 작은 학습 개념 단위가 필요했습니다. 따라서 category는 관리/표시용으로 두고, 추천 기준은 topic으로 설계했습니다.

#### Topic 후보 자동 반영을 피한 이유

LLM이나 키워드 추출 결과를 바로 `topics`에 넣으면 중복 topic, 애매한 topic, 과도하게 넓은 topic이 쌓일 수 있습니다. MVP에서는 수동 seed topic, keyword matching, LLM 보조 추출, 사람 검토를 결합한 하이브리드 방식을 선택했습니다.

#### RAG + Agent를 선택한 이유

순수 LLM만 사용하면 실제 보유 데이터에 없는 강의나 자료를 만들어낼 위험이 있습니다. 반대로 키워드 검색만 사용하면 사용자 목적, 수준, 기간, 학습 스타일을 충분히 반영하기 어렵습니다. RAG로 실제 데이터 기반성을 확보하고, Agent로 입력 분석/검색/생성/검증 단계를 분리했습니다.

#### 학습 일정 생성 시점

처음에는 커리큘럼 생성 시 전체 `learning_schedules`를 미리 만드는 방식을 고려했습니다. 하지만 사용자가 일시정지하거나 재개하면 미래 일정이 계속 어긋나는 문제가 생겼습니다.

최종 구현에서는 다음처럼 분리했습니다.

- `curriculum_steps`: AI가 만든 전체 학습 계획
- `curriculum_step_progresses`: 사용자의 step 진행 상태
- `learning_schedules`: 실제 시작한 step의 일정
- `learning_progresses`: 실제 학습 기록

상태 흐름:

- `curricula.status`: `DRAFT` -> `ACTIVE` -> `PAUSED` -> `ACTIVE` -> `COMPLETED`
- `curriculum_step_progresses.status`: `NOT_STARTED` -> `IN_PROGRESS` -> `PAUSED` -> `COMPLETED`
- `learning_schedules.status`: `PLANNED` -> `DONE` 또는 `CANCELLED`

### 구현하면서 학습한 점과 어려웠던 점

#### 1. LLM 결과를 그대로 믿으면 안 된다

AI가 생성한 커리큘럼은 자연어 품질이 좋아 보여도 실제 DB에 없는 강의나 자료 식별자를 포함할 수 있습니다. 이를 해결하기 위해 prompt 단계에서 사용 가능한 identifier를 제한하고, 생성 후 validator에서 다시 제거했습니다.

#### 2. 추천 품질은 모델보다 데이터 구조에 더 크게 의존한다

추천 결과를 개선하려면 더 큰 모델을 쓰는 것보다 topic 체계, alias, course/resource-topic 연결 품질을 높이는 것이 중요했습니다. 데이터 전처리와 검토 가능한 pipeline의 필요성을 배웠습니다.

#### 3. 계획 데이터와 실행 데이터는 분리해야 한다

커리큘럼은 계획이고, 학습 진행은 실제 사용자 행동입니다. 두 데이터를 같은 시점에 한 번에 생성하면 pause/resume, step 건너뛰기, 일정 변경에 취약합니다. 이 문제를 해결하기 위해 `curriculum_steps`와 `learning_schedules`를 분리했습니다.

#### 4. 긴 작업에는 사용자 피드백이 필요하다

AI 커리큘럼 생성은 검색과 LLM 호출이 포함되어 응답이 느릴 수 있습니다. 스트리밍 진행률과 문구를 제공하면서 사용자가 서비스가 멈춘 것이 아니라 처리 중임을 알 수 있게 했습니다.

#### 5. 프론트엔드와 백엔드 계약을 명확히 유지해야 한다

생성 API, 스트리밍 API, 저장 API가 분리되면서 프론트엔드가 어떤 응답을 preview로 보고 어떤 응답을 DB 저장 결과로 봐야 하는지 명확한 계약이 필요했습니다. 이 때문에 serializer, response normalizer, save service의 역할을 분리했습니다.

### 검증 기준

README 작성 시 실제 코드와 대조한 항목은 다음과 같습니다.

- Django URL과 README API 경로 일치
- 실제 앱 구조와 README 프로젝트 구조 일치
- 실제 모델 기준 ERD 테이블 정리
- AI 설정값과 README 환경 변수 일치
- RAG/Agent 흐름과 실제 `ai/agent` 코드 일치
- 커리큘럼 생성, 스트리밍, 저장, 학습 시작 흐름과 실제 service/view 코드 일치

