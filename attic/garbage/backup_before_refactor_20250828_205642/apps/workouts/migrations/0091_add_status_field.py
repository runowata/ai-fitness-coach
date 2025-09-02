from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('workouts', '0090_add_ai_analysis_jsonb'),
    ]
    
    operations = [
        migrations.AddField(
            model_name='workoutplan',
            name='status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('DRAFT', 'Draft'),
                    ('CONFIRMED', 'Confirmed'),
                    ('CANCELLED', 'Cancelled')
                ],
                default='DRAFT'
            ),
        ),
    ]