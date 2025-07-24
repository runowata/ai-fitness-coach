from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0004_add_exercise_timestamps_safe'),
    ]

    operations = [
        migrations.RunSQL(
            """
            ALTER TABLE exercises
                ADD COLUMN IF NOT EXISTS is_active boolean
                DEFAULT TRUE
                NOT NULL;
            """,
            reverse_sql="""
            ALTER TABLE exercises
                DROP COLUMN IF EXISTS is_active;
            """,
        ),
    ]
