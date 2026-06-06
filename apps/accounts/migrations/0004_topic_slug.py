from django.db import migrations, models
from django.utils.text import slugify


def make_unique_slug(name, used_slugs):
    base_slug = slugify(name, allow_unicode=True) or "topic"
    slug = base_slug
    index = 2

    while slug in used_slugs:
        slug = f"{base_slug}-{index}"
        index += 1

    used_slugs.add(slug)
    return slug


def add_and_populate_topic_slug(apps, schema_editor):
    Topic = apps.get_model("accounts", "Topic")
    table_name = Topic._meta.db_table
    column_name = "slug"

    with schema_editor.connection.cursor() as cursor:
        existing_columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(
                cursor,
                table_name,
            )
        }

    if column_name not in existing_columns:
        field = models.CharField(max_length=150, null=True, blank=True)
        field.set_attributes_from_name(column_name)
        schema_editor.add_field(Topic, field)

    used_slugs = set()
    topics = Topic.objects.order_by("id").values_list("id", "name")
    with schema_editor.connection.cursor() as cursor:
        for topic_id, name in topics:
            slug = make_unique_slug(name, used_slugs)
            cursor.execute(
                'UPDATE "topics" SET "slug" = %s WHERE "id" = %s',
                [slug, topic_id],
            )

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            'CREATE UNIQUE INDEX IF NOT EXISTS "topics_slug_unique" ON "topics" ("slug")'
        )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_userprofile_preferred_learning_style"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    add_and_populate_topic_slug,
                    migrations.RunPython.noop,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="topic",
                    name="slug",
                    field=models.CharField(max_length=150, unique=True),
                ),
            ],
        ),
    ]
