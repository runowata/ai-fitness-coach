from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("workouts", "0003_add_missing_exercise_video_cols"),
    ]

    operations = [
        # создаст колонку, ТОЛЬКО если её ещё нет — иначе тихо пропустит
        migrations.RunSQL(
            """
            ALTER TABLE exercises
              ADD COLUMN IF NOT EXISTS created_at timestamp with time zone
              NULL;
            """,
            reverse_sql="""
            ALTER TABLE exercises
              DROP COLUMN IF EXISTS created_at;
            """,
        ),
        migrations.RunSQL(
            """
            ALTER TABLE exercises
              ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone
              NULL;
            """,
            reverse_sql="""
            ALTER TABLE exercises
              DROP COLUMN IF EXISTS updated_at;
            """,
        ),
    ]
