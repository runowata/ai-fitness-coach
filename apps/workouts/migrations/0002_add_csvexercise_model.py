# Generated to add missing CSVExercise model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CSVExercise',
            fields=[
                ('id', models.CharField(primary_key=True, max_length=20)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('difficulty', models.CharField(max_length=20, default='beginner')),
                ('muscle_groups', models.JSONField(default=list)),
                ('equipment_needed', models.JSONField(default=list)),
                ('ai_tags', models.JSONField(default=list)),
                ('category', models.CharField(max_length=20, blank=True)),
                ('r2_slug', models.CharField(max_length=50, blank=True, help_text='Original R2 slug format')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'csv_exercises',
                'verbose_name': 'CSV Exercise',
                'verbose_name_plural': 'CSV Exercises',
            },
        ),
    ]