from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_initial_topics(apps, schema_editor):
    Topic = apps.get_model("accounts", "Topic")
    topic_names = [
        "Python",
        "Django",
        "Vue",
        "JavaScript",
        "SQL",
        "Data Analysis",
        "Machine Learning",
        "Deep Learning",
        "Linear Algebra",
        "English Listening",
    ]

    for name in topic_names:
        Topic.objects.get_or_create(
            name=name,
            defaults={
                "depth": 0,
                "topic_type": "SKILL",
                "is_learning_unit": True,
                "is_assessable": False,
                "is_active": True,
            },
        )


def remove_initial_topics(apps, schema_editor):
    Topic = apps.get_model("accounts", "Topic")
    Topic.objects.filter(
        name__in=[
            "Python",
            "Django",
            "Vue",
            "JavaScript",
            "SQL",
            "Data Analysis",
            "Machine Learning",
            "Deep Learning",
            "Linear Algebra",
            "English Listening",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Topic",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("depth", models.IntegerField(default=0)),
                ("topic_type", models.CharField(choices=[("CATEGORY", "Category"), ("SUBJECT", "Subject"), ("SKILL", "Skill")], default="SKILL", max_length=30)),
                ("is_learning_unit", models.BooleanField(default=True)),
                ("is_assessable", models.BooleanField(default=False)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("parent_topic", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="children", to="accounts.topic")),
            ],
            options={
                "db_table": "topics",
            },
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("available_weekly_hours", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "user_profiles",
            },
        ),
        migrations.CreateModel(
            name="UserInterestTopic",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("topic", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="interested_users", to="accounts.topic")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="interest_topics", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "user_interest_topics",
                "unique_together": {("user", "topic")},
            },
        ),
        migrations.RunPython(create_initial_topics, remove_initial_topics),
    ]
