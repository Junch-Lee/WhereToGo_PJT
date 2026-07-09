## 전체 데이터 구조 및 역할 분배

|제목|내용|설명|
|------|---|---|
|`final_topics_import.csv`|`Topics` 마스터 파일|서비스 전체 표준 학습 개념 사전|
|`final_topics_aliases_import.csv`|토픽 별칭 사전|사용자 or 강의 표현 정규화|
|`curriculum_courses.csv`|대학 강의계획서|학습 순서, 난이도, 선수지식 설계 근거|
|`learning_resources.csv`|강의 자료|사용자에게 추천 가능한 강의|
|`final_course_topics_import.csv`|강의계획서 - 토픽 매핑|`curriculum_courses`-`topics` 간 연결|
|`final_resource_topics_import.csv`|강의자료 - 토픽 매핑|`learning_resources`-`topics` 간 연결|


### 구조 표현

```text

                  final_topics_import.csv
                         │
         ┌───────────────┼────────────────┐
         │               │                │
    aliases.csv   course_topics.csv   resource_topics.csv
                         │                │
                         │                │
              curriculum_courses    learning_resources

```