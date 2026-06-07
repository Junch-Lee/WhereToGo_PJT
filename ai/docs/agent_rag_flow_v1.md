```text
[사용자 입력]

  ↓

[Analyze Input Node]
- 사용자 목표, 수준, 기간 분석
- 후보 topic 표현 도출

  ↓

[Topic Resolver Tool]
- aliases + final_topics_import 기준으로 topic_slug 정규화
- active topic만 사용
- learning_unit / assessable 속성 확인

  ↓

[RAG Retriever Tool]
- normalized topic 기반으로 curriculum_courses 검색
- normalized topic 기반으로 learning_resources 검색

  ↓

[Generate Curriculum Node]
- RAG 결과와 topic 구조를 기반으로 커리큘럼 생성

  ↓

[Trace + Output]
```