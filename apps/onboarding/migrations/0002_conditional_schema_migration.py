from django.db import migrations

def check_and_add_columns(apps, schema_editor):
    # Получаем таблицы из метаданных модели, а не хардкодом
    Question = apps.get_model('onboarding', 'OnboardingQuestion')
    Response = apps.get_model('onboarding', 'UserOnboardingResponse')
    question_table = Question._meta.db_table
    response_table = Response._meta.db_table
    qn = schema_editor.connection.ops.quote_name

    # Колонки которые нам потенциально нужны
    columns = [
        (question_table, "block_name", "varchar(100)"),
        (question_table, "block_order", "integer DEFAULT 1"),
        (question_table, "depends_on_answer", "varchar(100)"),
        (question_table, "depends_on_question_id", "integer"),
        (question_table, "is_block_separator", "boolean DEFAULT false"),
        (question_table, "scale_max_label", "varchar(50)"),
        (question_table, "scale_min_label", "varchar(50)"),
        (question_table, "separator_text", "text"),
        (response_table, "answer_body_map", "jsonb"),
        (response_table, "answer_scale", "integer"),
    ]

    with schema_editor.connection.cursor() as cursor:
        for table, column, sql_type in columns:
            # проверяем, есть ли колонка
            cursor.execute("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = %s
                  AND column_name = %s
            """, [table, column])
            exists = cursor.fetchone() is not None
            if exists:
                # уже есть — пропускаем
                continue

            # добавляем как NULL без дефолта (безопасно и без долгих locks)
            ddl = f'ALTER TABLE {qn(table)} ADD COLUMN {qn(column)} {sql_type};'
            cursor.execute(ddl)

def noop(*args, **kwargs):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(check_and_add_columns, reverse_migration),
    ]