# Generated manually to handle csv_exercises table creation
# This addresses the "relation already exists" issue by separating CSVExercise 
# from the initial migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name="CSVExercise",
            fields=[
                (
                    "id",
                    models.CharField(max_length=20, primary_key=True, serialize=False),
                ),
                ("name_ru", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
            ],
            options={
                "verbose_name": "Упражнение",
                "verbose_name_plural": "Упражнения", 
                "db_table": "csv_exercises",
            },
        ),
    ]