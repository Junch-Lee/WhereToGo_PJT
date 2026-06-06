## `Topics` 관련 규칙 설정

- `Topics` 데이터셋은 직접 임베딩하지 않고, 토픽 정규화 기준으로만 사용
    - 사용자 입력 뿐만 아니라, `topic_slug`, `aliases` 등을 이용해 쿼리를 안정적으로 변환 (검색 품질 안정화)

- (예시) : 추후 Agent 워크플로우에 `Topic Resolver Tool` 설정 

- 필드 별 정책

```
항목	                  정책
표준 ID	           topic_slug
계층 구조	       parent_topic_slug
토픽 깊이	       depth
토픽 유형	       topic_type
커리큘럼 step 후보   is_learning_unit=true 우선
진단 후보	       is_assessable=true 우선
사용 여부	       is_active=true만 사용
출처 관리	       source metadata로 보관
```
- 역할
1. LLM이 뽑은 후보 topic 표현을 topic_slug로 정규화

2. aliases.csv를 이용해 표현 흔들림 보정

3. parent_topic_slug/depth를 이용해 필요 시 상위·하위 topic 확인

4. is_learning_unit=true인 topic을 curriculum step 후보로 우선 선택