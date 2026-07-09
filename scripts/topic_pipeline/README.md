# Topic Pipeline Import

이 문서는 topic pipeline에서 생성한 최종 CSV fixture 데이터를 Django DB에
적재하는 방법을 정리한다.

우리 프로젝트의 로컬 DB 파일인 `db.sqlite3`는 git에 포함되지 않는다. 그래서
개발자마다 같은 topic 데이터를 사용하려면, 이 디렉터리에 있는 최종 CSV를 각자
로컬 DB에 import해야 한다.

## 전체 구조

최종 import 대상 CSV는 기본적으로 아래 디렉터리에 둔다.

```plain
scripts/topic_pipeline/data/final/
```

현재 import command는 이 디렉터리에서 아래 4개 파일을 읽는다.

```plain
final_topics_import.csv
final_topic_aliases_import.csv
final_course_topics_import.csv
final_resource_topics_import.csv
```

`final_resoucse_topics_import.csv`처럼 resource 철자가 틀린 예전 파일명도
fallback으로 지원한다. 다만 현재 기준 파일명은
`final_resource_topics_import.csv`이다.

## Import Command

사용하는 Django management command는 다음 파일에 있다.

```plain
apps/curriculum/management/commands/load_topic_fixtures.py
```

실행 명령은 다음과 같다.

```bash
python manage.py load_topic_fixtures
```

이 command는 CSV를 읽어서 아래 테이블에 데이터를 넣는다.

- `topics`
- `topic_aliases`
- `course_topics`
- `resource_topics`

동일한 command를 여러 번 실행해도 같은 row가 중복 생성되지 않도록
`update_or_create`와 unique key 기준의 upsert 방식으로 동작한다.

## 실행 전 준비

먼저 migration이 적용되어 있어야 한다.

```bash
python manage.py migrate
```

그 다음 dry-run으로 CSV 파일, header, FK 참조, 중복 row, 예상 생성/수정/skip
개수를 확인한다.

```bash
python manage.py load_topic_fixtures --dry-run
```

dry-run 결과에 `errors`가 없고, skip 내용이 의도한 범위라면 실제 import를
실행한다.

```bash
python manage.py load_topic_fixtures
```

추천 실행 순서는 다음과 같다.

```bash
python manage.py migrate
python manage.py load_topic_fixtures --dry-run
python manage.py load_topic_fixtures
```

## 옵션

### `--dry-run`

DB에 실제로 저장하지 않고 검증과 예상 결과만 출력한다.

```bash
python manage.py load_topic_fixtures --dry-run
```

확인하는 내용은 다음과 같다.

- 필수 CSV 파일이 모두 있는지
- 필수 column이 모두 있는지
- CSV row 수가 몇 개인지
- topic slug, alias, 연결 row가 중복되는지
- FK 대상 topic/course/resource를 찾을 수 있는지
- 실제 실행 시 생성/수정/skip/error가 몇 건일지

dry-run은 내부적으로 transaction을 rollback하므로 DB 데이터가 바뀌지 않는다.

### `--clear`

기존 topic fixture 데이터를 삭제한 뒤 다시 import한다.

```bash
python manage.py load_topic_fixtures --clear
```

삭제 순서는 FK 관계를 고려해 다음처럼 역순으로 진행된다.

```plain
resource_topics
course_topics
topic_aliases
topics
```

`--clear`는 기존 topic 관련 row를 지우는 작업이므로 주의해서 사용한다. 먼저
아래처럼 dry-run과 함께 실행해 삭제 예정 건수를 확인하는 것을 권장한다.

```bash
python manage.py load_topic_fixtures --dry-run --clear
```

### `--data-dir`

기본 경로가 아닌 다른 디렉터리의 CSV를 import할 때 사용한다.

```bash
python manage.py load_topic_fixtures --data-dir scripts/topic_pipeline/data/final/
```

다른 디렉터리를 지정하더라도 그 안에는 동일한 파일명 4개가 있어야 한다.

## CSV별 역할

### `final_topics_import.csv`

`topics` 테이블에 들어갈 기본 topic 데이터를 담는다.

주요 매핑은 다음과 같다.

- `topic_slug` -> `Topic.slug`
- `parent_topic_slug` -> `Topic.parent_topic`
- `name` -> `Topic.name`
- `depth` -> `Topic.depth`
- `topic_type` -> `Topic.topic_type`
- `is_learning_unit` -> `Topic.is_learning_unit`
- `is_assessable` -> `Topic.is_assessable`
- `description` -> `Topic.description`
- `is_active` -> `Topic.is_active`

`Topic.slug`를 기준으로 upsert한다. parent topic은 모든 topic row를 먼저 만든
뒤 `parent_topic_slug` 기준으로 연결한다.

### `final_topic_aliases_import.csv`

topic 검색과 매칭에 사용할 alias 데이터를 담는다.

주요 매핑은 다음과 같다.

- `topic_lookup_key` -> `Topic.slug`
- `alias_name` -> `TopicAlias.alias_name`
- `source` -> `TopicAlias.source`
- `language` -> `TopicAlias.language`
- `alias_type` -> `TopicAlias.alias_type`
- `match_policy` -> `TopicAlias.match_policy`
- `priority` -> `TopicAlias.priority`
- `note` -> `TopicAlias.note`

`TopicAlias`는 `(topic, alias_name, match_policy)` 조합을 기준으로 중복을 막는다.

### `final_course_topics_import.csv`

기존 `CurriculumCourse`와 `Topic`을 연결하는 데이터를 담는다.

주요 매핑은 다음과 같다.

- `curriculum_course_lookup_key` -> `CurriculumCourse.source_row_number`
- `topic_lookup_key` -> `Topic.slug`
- `relevance_score` -> `CourseTopic.relevance_score`
- `extraction_method` -> `CourseTopic.extraction_method`
- `is_primary` -> `CourseTopic.is_primary`
- `matched_fields` -> `CourseTopic.matched_fields`
- `match_types` -> `CourseTopic.match_types`
- `link_type` -> `CourseTopic.link_type`

course 또는 topic FK 대상을 찾지 못한 row는 import하지 않고 skip summary에
기록한다.

### `final_resource_topics_import.csv`

기존 `LearningResource`와 `Topic`을 연결하는 데이터를 담는다.

주요 매핑은 다음과 같다.

- `learning_resource_lookup_key` -> `LearningResource.lookup_key`
- `topic_lookup_key` -> `Topic.slug`
- `relevance_score` -> `ResourceTopic.relevance_score`
- `extraction_method` -> `ResourceTopic.extraction_method`
- `is_primary` -> `ResourceTopic.is_primary`
- `matched_fields` -> `ResourceTopic.matched_fields`
- `match_types` -> `ResourceTopic.match_types`
- `link_type` -> `ResourceTopic.link_type`

resource 또는 topic FK 대상을 찾지 못한 row는 import하지 않고 skip summary에
기록한다.

## Import 순서가 중요한 이유

CSV는 반드시 아래 순서로 처리한다.

```plain
topics
topic_aliases
course_topics
resource_topics
```

`topic_aliases`, `course_topics`, `resource_topics`는 모두 `topics`를 FK로
참조한다. 따라서 topics가 먼저 들어가야 뒤의 파일들이 topic을 찾을 수 있다.

course/resource 연결 테이블은 topic뿐 아니라 기존 `CurriculumCourse`,
`LearningResource`도 참조한다. 이 두 모델의 원본 row가 DB에 없으면 해당 연결
row는 만들 수 없으므로 skip된다.

## 결과 확인

import 후 row 수를 간단히 확인하려면 Django shell에서 다음 명령을 실행한다.

```bash
python manage.py shell -c "from apps.accounts.models import Topic, TopicAlias; from apps.curriculum.models import CourseTopic, ResourceTopic; print(Topic.objects.count(), TopicAlias.objects.count(), CourseTopic.objects.count(), ResourceTopic.objects.count())"
```

현재 최종 CSV 기준 row 수는 다음과 같다.

- topics CSV row: 142
- topic aliases CSV row: 210
- course topic links CSV row: 730
- resource topic links CSV row: 217

이미 DB에 seed 데이터가 있거나 FK 대상 데이터 상태가 다르면 실제 테이블 row 수는
CSV row 수와 다를 수 있다.
