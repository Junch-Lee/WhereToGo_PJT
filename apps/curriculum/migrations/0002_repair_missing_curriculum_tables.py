from django.db import migrations


def repair_missing_curriculum_tables(apps, schema_editor):
    """
    로컬 개발 DB에서 마이그레이션 기록과 실제 테이블 상태가 어긋난 경우를 복구한다.

    배경:
        현재 브랜치 작업 전후로 curriculum 앱의 0001_initial 마이그레이션이 적용된 것으로
        기록되어 있지만, 실제 SQLite DB에는 curricula, categories 같은 신규 테이블이 없는
        상태가 발생할 수 있다. 이 상태에서는 일반 migrate가 0001을 다시 실행하지 않으므로
        /api/curriculums/ 조회 시 no such table 오류가 발생한다.

    동작:
        - 새 DB처럼 0001이 정상 적용된 환경에서는 아무 작업도 하지 않는다.
        - 테이블이 빠진 로컬 DB에서는 빠진 테이블만 생성한다.
        - 기존 curriculum_courses 테이블이 남아 있는 경우에는 삭제하지 않고, 현재 모델에서
          필요한 description 컬럼만 없을 때 추가한다.
    """
    existing_tables = set(schema_editor.connection.introspection.table_names())

    model_names = [
        "Category",
        "LearningResource",
        "Curriculum",
        "CurriculumStep",
        "CurriculumCategory",
        "ResourceTopic",
        "CourseTopic",
        "CurriculumStepResource",
        "CurriculumStepCourse",
    ]

    for model_name in model_names:
        model = apps.get_model("curriculum", model_name)
        if model._meta.db_table not in existing_tables:
            schema_editor.create_model(model)
            existing_tables.add(model._meta.db_table)

    course_model = apps.get_model("curriculum", "CurriculumCourse")
    course_table = course_model._meta.db_table
    if course_table not in existing_tables:
        schema_editor.create_model(course_model)
        return

    existing_course_columns = {
        column.name
        for column in schema_editor.connection.introspection.get_table_description(
            schema_editor.connection.cursor(),
            course_table,
        )
    }

    if "description" not in existing_course_columns:
        schema_editor.add_field(course_model, course_model._meta.get_field("description"))


class Migration(migrations.Migration):

    dependencies = [
        ("curriculum", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            repair_missing_curriculum_tables,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
