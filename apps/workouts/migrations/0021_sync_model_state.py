# State-only migration to sync Django model state with actual database schema
# Fixes discrepancy where fields exist in database but Django doesn't know about them

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0020_add_is_active_to_csvexercise'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # No database operations - fields already exist
            ],
            state_operations=[
                # Remove constraint that was already dropped in 0020
                migrations.RemoveConstraint(
                    model_name='weeklylesson',
                    name='unique_weekly_lesson',
                ),
                
                # Add is_active field to CSVExercise (already exists in DB via RunPython in 0020)
                migrations.AddField(
                    model_name='csvexercise',
                    name='is_active',
                    field=models.BooleanField(default=True),
                ),
                
                # Add ai_analysis field to WorkoutPlan (already exists in DB via RunPython in 0011)
                migrations.AddField(
                    model_name='workoutplan',
                    name='ai_analysis',
                    field=models.JSONField(blank=True, null=True),
                ),
            ],
        ),
    ]