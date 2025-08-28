from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('workouts','0004_clean_exercise_model')]
    operations = [
        migrations.AddField(
            model_name='workoutplan',
            name='ai_analysis',
            field=models.JSONField(null=True, blank=True),
        ),
    ]