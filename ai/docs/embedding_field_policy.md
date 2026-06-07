## 1. `curriculum_courses` RAG 문서 정책 

```text
[대학 강의계획서] - 커리큘럼 단계 설정 과정에 주로 참고

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

- `mapped_topic_names` : `final_course_topics_import.csv` 를 통해 로드

## 2. `learning_resources` RAG 문서 정책

```text
[학습 자료]

자료명: {title}
분야: {main_category} > {sub_category}
난이도: {difficulty_level}
자료 유형: {content_type}

설명:
{description}

연결 토픽:
{mapped_topic_names}
```

- `mapped_topic_names` : `final_resource_topics_import.csv`를 통해 로드