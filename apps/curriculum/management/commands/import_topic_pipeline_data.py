import csv
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


DEFAULT_FINAL_DIR = Path("scripts/topic_pipeline/data/final")
DEFAULT_PROCESSED_DIR = Path("scripts/topic_pipeline/data/processed")

FINAL_FILES = {
    "topics": "final_topics_import.csv",
    "topic_aliases": "final_topic_aliases_import.csv",
    "course_topics": "final_course_topics_import.csv",
    "resource_topics": "final_resource_topics_import.csv",
}

PROCESSED_FILES = {
    "courses": "curriculum_courses_normalized.csv",
    "resources": "learning_resources_normalized.csv",
}


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def parse_bool(value):
    return clean(value).lower() in {"true", "1", "yes", "y"}


def parse_int(value, default=None):
    text = clean(value)
    if not text:
        return default
    try:
        return int(float(text))
    except ValueError:
        return default


def parse_decimal(value):
    text = clean(value)
    if not text:
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise CommandError(f"잘못된 decimal 값입니다: {text}") from exc


def read_csv(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


class Command(BaseCommand):
    help = "topic pipeline CSV 데이터를 실제 CurriculumCourse/LearningResource/Topic 테이블에 import합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-dir",
            default=str(DEFAULT_FINAL_DIR),
            help="final_*_import.csv 파일들이 있는 디렉터리입니다.",
        )
        parser.add_argument(
            "--processed-dir",
            default=None,
            help="normalized course/resource CSV 파일들이 있는 디렉터리입니다.",
        )
        parser.add_argument(
            "--clear-topic-links",
            action="store_true",
            help="TopicAlias, CourseTopic, ResourceTopic만 지운 뒤 다시 연결합니다.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        final_dir = Path(options["data_dir"])
        processed_dir = self.resolve_processed_dir(final_dir, options["processed_dir"])

        final_rows = self.load_final_rows(final_dir)
        processed_rows = self.load_processed_rows(processed_dir)

        if options["clear_topic_links"]:
            ResourceTopic.objects.all().delete()
            CourseTopic.objects.all().delete()
            TopicAlias.objects.all().delete()

        stats = {
            "courses": self.import_courses(processed_rows["courses"]),
            "resources": self.import_resources(processed_rows["resources"]),
            "topics": self.import_topics(final_rows["topics"]),
            "aliases": self.import_aliases(final_rows["topic_aliases"]),
            "course_fallbacks": self.ensure_courses_from_links(final_rows["course_topics"]),
            "resource_fallbacks": self.ensure_resources_from_links(final_rows["resource_topics"]),
            "course_topics": self.import_course_topics(final_rows["course_topics"]),
            "resource_topics": self.import_resource_topics(final_rows["resource_topics"]),
        }

        self.stdout.write(self.style.SUCCESS("topic pipeline 데이터 import 완료"))
        for name, count in stats.items():
            self.stdout.write(f"- {name}: {count}")

    def load_final_rows(self, data_dir):
        rows = {}
        missing = []
        for key, filename in FINAL_FILES.items():
            path = data_dir / filename
            if not path.exists():
                missing.append(str(path))
            rows[key] = read_csv(path)

        if missing:
            raise CommandError("필수 final CSV 파일이 없습니다: " + ", ".join(missing))

        return rows

    def resolve_processed_dir(self, final_dir, option_value):
        if option_value:
            return Path(option_value)

        has_processed_files = all(
            (final_dir / filename).exists()
            for filename in PROCESSED_FILES.values()
        )
        if has_processed_files:
            return final_dir

        if final_dir == DEFAULT_FINAL_DIR:
            return DEFAULT_PROCESSED_DIR

        return final_dir

    def load_processed_rows(self, processed_dir):
        return {
            key: read_csv(processed_dir / filename)
            for key, filename in PROCESSED_FILES.items()
        }

    def import_courses(self, rows):
        count = 0
        for row in rows:
            source_row_number = parse_int(row.get("source_row_number"))
            course_name = clean(row.get("course_name"))
            if source_row_number is None or not course_name:
                continue

            CurriculumCourse.objects.update_or_create(
                source_row_number=source_row_number,
                defaults={
                    "course_name": course_name,
                    "university_name": clean(row.get("university_name")),
                    "department_name": clean(row.get("department_name")),
                    "grade": parse_int(row.get("grade")),
                    "semester": clean(row.get("semester")),
                    "learning_objective": clean(row.get("learning_objective")),
                    "description": clean(row.get("learning_objective")),
                },
            )
            count += 1
        return count

    def import_resources(self, rows):
        count = 0
        for row in rows:
            lookup_key = clean(row.get("external_id"))
            title = clean(row.get("title"))
            if not lookup_key or not title:
                continue

            LearningResource.objects.update_or_create(
                lookup_key=lookup_key,
                defaults={
                    "title": title,
                    "description": clean(row.get("description")),
                    "url": clean(row.get("url")),
                    "provider": clean(row.get("source_type")),
                    "provider_name": clean(row.get("provider_name")),
                    "instructor_name": clean(row.get("instructor_name")),
                    "resource_type": clean(row.get("content_type")),
                    "difficulty_level": clean(row.get("difficulty_level")),
                },
            )
            count += 1
        return count

    def import_topics(self, rows):
        count = 0
        topic_by_slug = {topic.slug: topic for topic in Topic.objects.all()}

        for row in rows:
            slug = clean(row.get("topic_slug"))
            if not slug:
                continue

            topic, _ = Topic.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": clean(row.get("name")) or slug,
                    "depth": parse_int(row.get("depth"), 0),
                    "topic_type": clean(row.get("topic_type")) or Topic.TopicType.SKILL,
                    "is_learning_unit": parse_bool(row.get("is_learning_unit")),
                    "is_assessable": parse_bool(row.get("is_assessable")),
                    "description": clean(row.get("description")),
                    "is_active": parse_bool(row.get("is_active")) if clean(row.get("is_active")) else True,
                },
            )
            topic_by_slug[slug] = topic
            count += 1

        for row in rows:
            slug = clean(row.get("topic_slug"))
            parent_slug = clean(row.get("parent_topic_slug"))
            if not slug:
                continue
            Topic.objects.filter(slug=slug).update(
                parent_topic=topic_by_slug.get(parent_slug) if parent_slug else None
            )

        return count

    def import_aliases(self, rows):
        count = 0
        topic_by_slug = {topic.slug: topic for topic in Topic.objects.all()}
        for row in rows:
            topic = topic_by_slug.get(clean(row.get("topic_lookup_key")))
            alias_name = clean(row.get("alias_name"))
            match_policy = clean(row.get("match_policy"))
            if not topic or not alias_name or not match_policy:
                continue

            TopicAlias.objects.update_or_create(
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
            count += 1
        return count

    def ensure_courses_from_links(self, rows):
        count = 0
        for row in rows:
            source_row_number = parse_int(row.get("curriculum_course_lookup_key"))
            if source_row_number is None:
                continue

            _, created = CurriculumCourse.objects.get_or_create(
                source_row_number=source_row_number,
                defaults={
                    "course_name": clean(row.get("course_name")) or f"Course {source_row_number}",
                },
            )
            if created:
                count += 1
        return count

    def ensure_resources_from_links(self, rows):
        count = 0
        for row in rows:
            lookup_key = clean(row.get("learning_resource_lookup_key"))
            if not lookup_key:
                continue

            _, created = LearningResource.objects.get_or_create(
                lookup_key=lookup_key,
                defaults={
                    "title": clean(row.get("title")) or lookup_key,
                },
            )
            if created:
                count += 1
        return count

    def import_course_topics(self, rows):
        count = 0
        topic_by_slug = {topic.slug: topic for topic in Topic.objects.all()}
        course_by_number = {
            str(course.source_row_number): course
            for course in CurriculumCourse.objects.exclude(source_row_number__isnull=True)
        }

        for row in rows:
            course = course_by_number.get(clean(row.get("curriculum_course_lookup_key")))
            topic = topic_by_slug.get(clean(row.get("topic_lookup_key")))
            if not course or not topic:
                continue

            CourseTopic.objects.update_or_create(
                curriculum_course=course,
                topic=topic,
                defaults=self.link_defaults(row),
            )
            count += 1
        return count

    def import_resource_topics(self, rows):
        count = 0
        topic_by_slug = {topic.slug: topic for topic in Topic.objects.all()}
        resource_by_key = {
            resource.lookup_key: resource
            for resource in LearningResource.objects.exclude(lookup_key__isnull=True)
        }

        for row in rows:
            resource = resource_by_key.get(clean(row.get("learning_resource_lookup_key")))
            topic = topic_by_slug.get(clean(row.get("topic_lookup_key")))
            if not resource or not topic:
                continue

            ResourceTopic.objects.update_or_create(
                learning_resource=resource,
                topic=topic,
                defaults=self.link_defaults(row),
            )
            count += 1
        return count

    def link_defaults(self, row):
        return {
            "relevance_score": parse_decimal(row.get("relevance_score")),
            "extraction_method": clean(row.get("extraction_method")),
            "is_primary": parse_bool(row.get("is_primary")),
            "matched_fields": clean(row.get("matched_fields")),
            "match_types": clean(row.get("match_types")),
            "link_type": clean(row.get("link_type")),
        }
