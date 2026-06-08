import csv
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import Topic, TopicAlias
from apps.curriculum.models import (
    CourseTopic,
    CurriculumCourse,
    LearningResource,
    ResourceTopic,
)


DEFAULT_DATA_DIR = Path("scripts/topic_pipeline/data/final")

FILES = {
    "topics": "final_topics_import.csv",
    "topic_aliases": "final_topic_aliases_import.csv",
    "course_topics": "final_course_topics_import.csv",
    "resource_topics": "final_resource_topics_import.csv",
}

LEGACY_RESOURCE_FILE = "final_resoucse_topics_import.csv"

REQUIRED_COLUMNS = {
    "topics": {
        "topic_slug",
        "name",
        "depth",
        "topic_type",
        "is_learning_unit",
        "is_assessable",
        "is_active",
    },
    "topic_aliases": {
        "topic_lookup_key",
        "alias_name",
        "match_policy",
    },
    "course_topics": {
        "curriculum_course_lookup_key",
        "topic_lookup_key",
    },
    "resource_topics": {
        "learning_resource_lookup_key",
        "topic_lookup_key",
    },
}


@dataclass
class ImportStats:
    """CSV 파일별 dry-run 예상치와 실제 저장 결과를 함께 기록하는 통계 객체."""

    rows: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    messages: list[str] = field(default_factory=list)

    def add_error(self, message):
        self.errors += 1
        self.messages.append(message)

    def add_skip(self, message):
        self.skipped += 1
        self.messages.append(message)


def clean(value):
    """CSV 셀 값을 검증과 모델 저장 전에 공백이 제거된 문자열로 정규화한다."""
    if value is None:
        return ""
    return str(value).strip()


def parse_bool(value):
    """CSV에 들어 있는 일반적인 boolean 문자열을 BooleanField 값으로 변환한다."""
    return clean(value).lower() in {"true", "1", "yes", "y"}


def parse_int(value, default=0):
    """CSV 정수 값을 파싱하되, 선택 값이 비어 있으면 기본값을 사용한다."""
    text = clean(value)
    if not text:
        return default
    return int(text)


def parse_decimal(value):
    """CSV의 선택적 DecimalField 값을 파싱한다."""
    text = clean(value)
    if not text:
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        raise ValueError(f"유효하지 않은 decimal 값입니다: {text}")


class Command(BaseCommand):
    """
    topic pipeline 최종 CSV fixture 데이터를 Django DB에 적재한다.

    이 command는 topic pipeline이 생성한 최종 CSV가 초기 topic seed 데이터의
    기준이기 때문에 필요하다. FK 관계를 안전하게 맞추기 위해 topics,
    topic aliases, course-topic 연결, resource-topic 연결 순서로 4개 파일을
    읽는다. aliases와 연결 테이블은 topics를 참조하므로 이 순서가 중요하다.
    연결 row는 기존 CurriculumCourse와 LearningResource도 참조하므로, course나
    resource FK 대상이 없으면 조용히 무시하지 않고 summary에 기록한 뒤 skip한다.

    외부 ERD와 현재 Django 모델이 다를 경우 실제 DB 반영 기준은 Django 모델과
    migration이다. 이 command에서 사용하는 모델 매핑은 다음과 같다.

    - final_topics_import.csv -> Topic.slug, parent_topic.slug, name, depth,
      topic_type, is_learning_unit, is_assessable, description, is_active
    - final_topic_aliases_import.csv -> TopicAlias의
      (topic, alias_name, match_policy)
    - final_course_topics_import.csv -> CourseTopic의
      (CurriculumCourse.source_row_number, Topic.slug)
    - final_resource_topics_import.csv -> ResourceTopic의
      (LearningResource.lookup_key, Topic.slug)

    중복 적재를 막기 위해 update_or_create와 unique 관계 검증을 사용한다.
    --dry-run은 DB 저장 없이 파일, header, 중복 row, FK 참조, 생성/수정/skip
    예상 개수를 검증한다. --clear는 재적재 전에 topic 관련 fixture 데이터를
    FK 역순으로 삭제하므로, 기존 row를 지우는 작업이라는 점을 주의해야 한다.
    """

    help = "최종 topic pipeline CSV fixture를 topic 관련 테이블에 적재합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="DB에 저장하지 않고 검증 결과와 예상 변경 사항만 출력합니다.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="적재 전에 기존 topic fixture row를 삭제합니다.",
        )
        parser.add_argument(
            "--data-dir",
            default=str(DEFAULT_DATA_DIR),
            help="최종 topic pipeline CSV 파일이 들어 있는 디렉터리입니다.",
        )

    def handle(self, *args, **options):
        data_dir = Path(options["data_dir"])
        dry_run = options["dry_run"]
        clear = options["clear"]

        file_paths = self.validate_required_files(data_dir)
        rows_by_name = {
            name: self.read_csv(path)
            for name, path in file_paths.items()
        }
        self.validate_headers(rows_by_name)

        with transaction.atomic():
            clear_counts = {}
            if clear:
                clear_counts = self.clear_existing_data(dry_run=dry_run)

            stats = {
                "topics": self.load_topics(rows_by_name["topics"], dry_run=dry_run),
                "topic_aliases": self.load_topic_aliases(
                    rows_by_name["topic_aliases"],
                    dry_run=dry_run,
                ),
                "course_topics": self.load_course_topics(
                    rows_by_name["course_topics"],
                    dry_run=dry_run,
                ),
                "resource_topics": self.load_resource_topics(
                    rows_by_name["resource_topics"],
                    dry_run=dry_run,
                ),
            }

            has_errors = any(item.errors for item in stats.values())
            if dry_run or has_errors:
                transaction.set_rollback(True)

        self.print_summary(stats, file_paths, clear_counts, dry_run=dry_run)
        if has_errors:
            raise CommandError("Topic fixture import가 검증 오류와 함께 종료되었습니다.")

    def validate_required_files(self, data_dir):
        """필수 CSV 경로를 확인하고, 누락된 파일명을 명확히 알려주며 실패한다."""
        paths = {}
        missing = []

        for name, filename in FILES.items():
            path = data_dir / filename
            if name == "resource_topics" and not path.exists():
                legacy_path = data_dir / LEGACY_RESOURCE_FILE
                if legacy_path.exists():
                    path = legacy_path
            if not path.exists():
                missing.append(str(path))
            else:
                paths[name] = path

        if missing:
            raise CommandError("필수 CSV 파일이 없습니다: " + ", ".join(missing))

        return paths

    def read_csv(self, file_path):
        """fixture 데이터에 한국어가 포함될 수 있으므로 utf-8-sig로 CSV를 읽는다."""
        with file_path.open(encoding="utf-8-sig", newline="") as csv_file:
            return list(csv.DictReader(csv_file))

    def validate_headers(self, rows_by_name):
        """실제 CSV header를 기준으로 필수 column이 모두 있는지 확인한다."""
        errors = []
        for name, rows in rows_by_name.items():
            headers = set(rows[0].keys()) if rows else set()
            missing = sorted(REQUIRED_COLUMNS[name] - headers)
            if missing:
                errors.append(f"{FILES[name]}에 누락된 column: {', '.join(missing)}")

        if errors:
            raise CommandError("; ".join(errors))

    def clear_existing_data(self, dry_run):
        """
        fixture 테이블을 FK 역순으로 삭제한다.

        삭제 순서는 ResourceTopic, CourseTopic, TopicAlias, Topic이다. topics를
        먼저 삭제하면 cascade로 aliases/link table이 함께 지워져 각 테이블에서
        명시적으로 삭제되는 row 수를 확인하기 어렵다.
        """
        targets = [
            ("resource_topics", ResourceTopic),
            ("course_topics", CourseTopic),
            ("topic_aliases", TopicAlias),
            ("topics", Topic),
        ]
        counts = {name: model.objects.count() for name, model in targets}
        for _, model in targets:
            model.objects.all().delete()
        return counts

    def load_topics(self, rows, dry_run):
        """Topic row를 slug 기준으로 upsert한 뒤 parent slug로 parent_topic을 연결한다."""
        stats = ImportStats(rows=len(rows))
        seen = set()
        incoming_slugs = {clean(row.get("topic_slug")) for row in rows}
        existing = {topic.slug: topic for topic in Topic.objects.all()}

        for index, row in enumerate(rows, start=2):
            slug = clean(row.get("topic_slug"))
            if not slug:
                stats.add_error(f"topics row {index}: topic_slug는 필수입니다")
                continue
            if slug in seen:
                stats.add_skip(f"topics row {index}: 중복 topic_slug '{slug}'")
                continue
            seen.add(slug)

            required_error = self.find_blank_required(row, REQUIRED_COLUMNS["topics"])
            if required_error:
                stats.add_error(f"topics row {index}: {required_error}")
                continue

            parent_slug = clean(row.get("parent_topic_slug"))
            if parent_slug and parent_slug not in incoming_slugs and parent_slug not in existing:
                stats.add_error(
                    f"topics row {index}: parent_topic_slug '{parent_slug}'를 찾을 수 없습니다"
                )
                continue

            try:
                defaults = {
                    "name": clean(row.get("name")),
                    "depth": parse_int(row.get("depth")),
                    "topic_type": clean(row.get("topic_type")),
                    "is_learning_unit": parse_bool(row.get("is_learning_unit")),
                    "is_assessable": parse_bool(row.get("is_assessable")),
                    "description": clean(row.get("description")),
                    "is_active": parse_bool(row.get("is_active")),
                }
            except ValueError as exc:
                stats.add_error(f"topics row {index}: {exc}")
                continue

            topic, created = Topic.objects.update_or_create(slug=slug, defaults=defaults)
            if created:
                stats.created += 1
            else:
                stats.updated += 1
            existing[slug] = topic

        if stats.errors:
            return stats

        for row in rows:
            slug = clean(row.get("topic_slug"))
            parent_slug = clean(row.get("parent_topic_slug"))
            if not slug or slug not in existing:
                continue
            parent_topic = existing.get(parent_slug) if parent_slug else None
            Topic.objects.filter(slug=slug).update(parent_topic=parent_topic)

        return stats

    def load_topic_aliases(self, rows, dry_run):
        """TopicAlias row를 모델의 unique key 기준으로 upsert한다."""
        stats = ImportStats(rows=len(rows))
        seen = set()
        topic_by_slug = {topic.slug: topic for topic in Topic.objects.all()}

        for index, row in enumerate(rows, start=2):
            required_error = self.find_blank_required(
                row,
                REQUIRED_COLUMNS["topic_aliases"],
            )
            if required_error:
                stats.add_error(f"topic_aliases row {index}: {required_error}")
                continue

            topic_slug = clean(row.get("topic_lookup_key"))
            topic = topic_by_slug.get(topic_slug)
            if not topic:
                stats.add_error(
                    f"topic_aliases row {index}: topic_lookup_key '{topic_slug}'를 찾을 수 없습니다"
                )
                continue

            alias_name = clean(row.get("alias_name"))
            match_policy = clean(row.get("match_policy"))
            key = (topic.id, alias_name, match_policy)
            if key in seen:
                stats.add_skip(
                    f"topic_aliases row {index}: topic '{topic_slug}'의 중복 alias '{alias_name}'"
                )
                continue
            seen.add(key)

            _, created = TopicAlias.objects.update_or_create(
                topic=topic,
                alias_name=alias_name,
                match_policy=match_policy,
                defaults={
                    "source": clean(row.get("source")),
                    "language": clean(row.get("language")),
                    "alias_type": clean(row.get("alias_type")),
                    "priority": clean(row.get("priority")),
                    "note": clean(row.get("note")),
                },
            )
            if created:
                stats.created += 1
            else:
                stats.updated += 1

        return stats

    def load_course_topics(self, rows, dry_run):
        """course와 topic FK를 검증한 뒤 course-topic 연결 row를 upsert한다."""
        stats = ImportStats(rows=len(rows))
        seen = set()
        topic_by_slug = {topic.slug: topic for topic in Topic.objects.all()}
        course_by_source = {
            str(course.source_row_number): course
            for course in CurriculumCourse.objects.exclude(source_row_number__isnull=True)
        }

        for index, row in enumerate(rows, start=2):
            required_error = self.find_blank_required(
                row,
                REQUIRED_COLUMNS["course_topics"],
            )
            if required_error:
                stats.add_skip(f"course_topics row {index}: {required_error}")
                continue

            topic_slug = clean(row.get("topic_lookup_key"))
            course_key = clean(row.get("curriculum_course_lookup_key"))
            topic = topic_by_slug.get(topic_slug)
            course = course_by_source.get(course_key)
            if not topic:
                stats.add_skip(
                    f"course_topics row {index}: topic_lookup_key '{topic_slug}'를 찾을 수 없습니다"
                )
                continue
            if not course:
                stats.add_skip(
                    f"course_topics row {index}: curriculum_course_lookup_key '{course_key}'를 찾을 수 없습니다"
                )
                continue

            key = (course.id, topic.id)
            if key in seen:
                stats.add_skip(
                    f"course_topics row {index}: 중복 연결 course={course_key}, topic={topic_slug}"
                )
                continue
            seen.add(key)

            try:
                defaults = self.build_link_defaults(row)
            except ValueError as exc:
                stats.add_skip(f"course_topics row {index}: {exc}")
                continue

            _, created = CourseTopic.objects.update_or_create(
                curriculum_course=course,
                topic=topic,
                defaults=defaults,
            )
            if created:
                stats.created += 1
            else:
                stats.updated += 1

        return stats

    def load_resource_topics(self, rows, dry_run):
        """resource와 topic FK를 검증한 뒤 resource-topic 연결 row를 upsert한다."""
        stats = ImportStats(rows=len(rows))
        seen = set()
        topic_by_slug = {topic.slug: topic for topic in Topic.objects.all()}
        resource_by_lookup = {
            resource.lookup_key: resource
            for resource in LearningResource.objects.exclude(lookup_key__isnull=True)
        }

        for index, row in enumerate(rows, start=2):
            required_error = self.find_blank_required(
                row,
                REQUIRED_COLUMNS["resource_topics"],
            )
            if required_error:
                stats.add_skip(f"resource_topics row {index}: {required_error}")
                continue

            topic_slug = clean(row.get("topic_lookup_key"))
            resource_key = clean(row.get("learning_resource_lookup_key"))
            topic = topic_by_slug.get(topic_slug)
            resource = resource_by_lookup.get(resource_key)
            if not topic:
                stats.add_skip(
                    f"resource_topics row {index}: topic_lookup_key '{topic_slug}'를 찾을 수 없습니다"
                )
                continue
            if not resource:
                stats.add_skip(
                    f"resource_topics row {index}: learning_resource_lookup_key '{resource_key}'를 찾을 수 없습니다"
                )
                continue

            key = (resource.id, topic.id)
            if key in seen:
                stats.add_skip(
                    f"resource_topics row {index}: 중복 연결 resource={resource_key}, topic={topic_slug}"
                )
                continue
            seen.add(key)

            try:
                defaults = self.build_link_defaults(row)
            except ValueError as exc:
                stats.add_skip(f"resource_topics row {index}: {exc}")
                continue

            _, created = ResourceTopic.objects.update_or_create(
                learning_resource=resource,
                topic=topic,
                defaults=defaults,
            )
            if created:
                stats.created += 1
            else:
                stats.updated += 1

        return stats

    def build_link_defaults(self, row):
        """course/resource topic 연결 모델이 공유하는 metadata defaults를 만든다."""
        return {
            "relevance_score": parse_decimal(row.get("relevance_score")),
            "extraction_method": clean(row.get("extraction_method")),
            "is_primary": parse_bool(row.get("is_primary")),
            "matched_fields": clean(row.get("matched_fields")),
            "match_types": clean(row.get("match_types")),
            "link_type": clean(row.get("link_type")),
        }

    def find_blank_required(self, row, required_columns):
        """CSV 필수 값이 비어 있으면 검증 메시지를 반환한다."""
        for column in sorted(required_columns):
            if not clean(row.get(column)):
                return f"{column}는 필수입니다"
        return ""

    def print_summary(self, stats, file_paths, clear_counts, dry_run):
        """Django command 출력 helper를 사용해 간결한 import 결과를 출력한다."""
        title = "[Topic Fixture Import 요약]"
        if dry_run:
            title += " (dry-run)"
        self.stdout.write("")
        self.stdout.write(title)
        self.stdout.write("")

        self.stdout.write("파일")
        for name, path in file_paths.items():
            self.stdout.write(f"- {name}: {path}")
        self.stdout.write("")

        if clear_counts:
            self.stdout.write(self.style.WARNING("clear"))
            for name, count in clear_counts.items():
                verb = "삭제 예정" if dry_run else "삭제됨"
                self.stdout.write(f"- {name}: {verb} {count}")
            self.stdout.write("")

        for name in ("topics", "topic_aliases", "course_topics", "resource_topics"):
            item = stats[name]
            writer = self.stdout.write
            if item.errors:
                writer = lambda text, writer=writer: writer(self.style.ERROR(text))
            elif item.skipped:
                writer = lambda text, writer=writer: writer(self.style.WARNING(text))

            writer(name)
            self.stdout.write(f"- rows: {item.rows}")
            self.stdout.write(f"- created: {item.created}")
            self.stdout.write(f"- updated: {item.updated}")
            self.stdout.write(f"- skipped: {item.skipped}")
            self.stdout.write(f"- errors: {item.errors}")
            for message in item.messages[:20]:
                self.stdout.write(f"  - {message}")
            if len(item.messages) > 20:
                self.stdout.write(f"  - ... {len(item.messages) - 20} more")
            self.stdout.write("")
