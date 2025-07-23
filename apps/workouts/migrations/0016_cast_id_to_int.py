from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('workouts', '0006_alter_dailyworkout_options_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            """
            -- Просто меняем тип id на integer в PostgreSQL
            ALTER TABLE workouts_exercise 
                ALTER COLUMN id TYPE integer USING id::integer;
            """,
            reverse_sql="""
            -- Откат: обратно в varchar
            ALTER TABLE workouts_exercise 
                ALTER COLUMN id TYPE varchar(36);
            """
        ),
    ]