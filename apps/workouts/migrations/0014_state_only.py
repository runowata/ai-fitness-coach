# Generated manually to sync Django state with raw SQL operations in 0013_v2_schema

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    State-only migration to synchronize Django's migration state with 
    database schema changes made via raw SQL in 0013_v2_schema.
    
    This prevents Django from generating unnecessary migrations for 
    fields that already exist in the database.
    """

    dependencies = [
        ('workouts', '0013_v2_schema'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # No actual database changes - schema already updated by raw SQL
            ],
            state_operations=[
                # Sync state with fields added via raw SQL in 0013_v2_schema
                migrations.AddField(
                    model_name='exercise',
                    name='equipment',
                    field=models.CharField(default='bodyweight', help_text='Основной инвентарь: bodyweight | dumbbell | barbell …', max_length=50),
                ),
                migrations.AddField(
                    model_name='exercise',
                    name='poster_image',
                    field=models.ImageField(blank=True, help_text='Poster image for video player', null=True, upload_to='photos/workout/'),
                ),
                migrations.AddField(
                    model_name='videoclip',
                    name='r2_kind',
                    field=models.CharField(choices=[('technique', 'Technique'), ('mistake', 'Common Mistake'), ('instruction', 'Instruction'), ('intro', 'Introduction'), ('weekly', 'Weekly Motivation'), ('closing', 'Closing'), ('reminder', 'Reminder'), ('explain', 'Exercise Explanation')], default='technique', help_text='Video type for R2 organization', max_length=20),
                    preserve_default=False,
                ),
                migrations.AddField(
                    model_name='videoclip',
                    name='r2_file',
                    field=models.FileField(blank=True, help_text='Video file in R2 storage', null=True, upload_to='videos/'),
                ),
                migrations.AddField(
                    model_name='videoclip',
                    name='r2_archetype',
                    field=models.CharField(blank=True, choices=[('peer', 'Ровесник'), ('professional', 'Успешный профессионал'), ('mentor', 'Мудрый наставник')], max_length=20),
                ),
                migrations.AddField(
                    model_name='videoclip',
                    name='script_text',
                    field=models.TextField(blank=True, help_text='Video script/transcript for R2 videos'),
                ),
                migrations.AddField(
                    model_name='videoclip',
                    name='is_placeholder',
                    field=models.BooleanField(default=False, help_text='Whether this is a placeholder entry'),
                ),
                migrations.AddField(
                    model_name='workoutplan',
                    name='ai_analysis',
                    field=models.JSONField(blank=True, null=True),
                ),
                # Remove legacy fields that were dropped via raw SQL
                migrations.RemoveField(
                    model_name='exercise',
                    name='mistake_video_url',
                ),
                migrations.RemoveField(
                    model_name='exercise',
                    name='technique_video_url',
                ),
                migrations.RemoveField(
                    model_name='videoclip',
                    name='type',
                ),
                migrations.RemoveField(
                    model_name='videoclip',
                    name='url',
                ),
            ],
        ),
    ]