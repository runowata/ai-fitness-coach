# Generated to safely apply migrations with conflict checks
# Replaces 0002_onboardingquestion_block_name_and_more.py

import django.db.models.deletion
from django.db import migrations, models, connection


def check_column_exists(table_name, column_name):
    """Check if a column exists in the table"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            );
        """, [table_name, column_name])
        return cursor.fetchone()[0]


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0001_initial'),
    ]

    operations = []
    
    def __init__(self, name, app_label):
        super().__init__(name, app_label)
        
        # Only add operations for columns that don't exist yet
        if not check_column_exists('onboarding_questions', 'block_name'):
            self.operations.extend([
                migrations.AddField(
                    model_name='onboardingquestion',
                    name='block_name',
                    field=models.CharField(blank=True, max_length=100),
                ),
                migrations.AddField(
                    model_name='onboardingquestion',
                    name='block_order',
                    field=models.PositiveIntegerField(default=1),
                ),
                migrations.AddField(
                    model_name='onboardingquestion',
                    name='depends_on_answer',
                    field=models.CharField(blank=True, max_length=100),
                ),
                migrations.AddField(
                    model_name='onboardingquestion',
                    name='depends_on_question',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dependent_questions', to='onboarding.onboardingquestion'),
                ),
                migrations.AddField(
                    model_name='onboardingquestion',
                    name='is_block_separator',
                    field=models.BooleanField(default=False),
                ),
                migrations.AddField(
                    model_name='onboardingquestion',
                    name='scale_max_label',
                    field=models.CharField(blank=True, max_length=50),
                ),
                migrations.AddField(
                    model_name='onboardingquestion',
                    name='scale_min_label',
                    field=models.CharField(blank=True, max_length=50),
                ),
                migrations.AddField(
                    model_name='onboardingquestion',
                    name='separator_text',
                    field=models.TextField(blank=True),
                ),
                migrations.AddField(
                    model_name='useronboardingresponse',
                    name='answer_body_map',
                    field=models.JSONField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='useronboardingresponse',
                    name='answer_scale',
                    field=models.IntegerField(blank=True, null=True),
                ),
                migrations.AlterField(
                    model_name='onboardingquestion',
                    name='question_type',
                    field=models.CharField(choices=[('single_choice', 'Single Choice'), ('multiple_choice', 'Multiple Choice'), ('number', 'Number Input'), ('text', 'Text Input'), ('scale', 'Scale (1-5)'), ('body_map', 'Body Map Selection')], max_length=20),
                ),
            ])