# Remove unnecessary category field from CSVExercise

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0004_add_missing_csvexercise_columns'),
    ]

    operations = [
        # Remove category field - not needed as we can determine it from ID prefix
        migrations.RunSQL(
            sql="ALTER TABLE csv_exercises DROP COLUMN IF EXISTS category;",
            reverse_sql="ALTER TABLE csv_exercises ADD COLUMN category VARCHAR(20) DEFAULT '';",
        ),
    ]