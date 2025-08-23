import django.db.models.deletion
from django.db import migrations, models

SQL = """
ALTER TABLE public.onboarding_questions
    ADD COLUMN IF NOT EXISTS block_name varchar(100),
    ADD COLUMN IF NOT EXISTS block_order integer,
    ADD COLUMN IF NOT EXISTS depends_on_answer varchar(100),
    ADD COLUMN IF NOT EXISTS depends_on_question_id integer,
    ADD COLUMN IF NOT EXISTS is_block_separator boolean,
    ADD COLUMN IF NOT EXISTS scale_max_label varchar(50),
    ADD COLUMN IF NOT EXISTS scale_min_label varchar(50),
    ADD COLUMN IF NOT EXISTS separator_text text;

ALTER TABLE public.user_onboarding_responses
    ADD COLUMN IF NOT EXISTS answer_body_map jsonb,
    ADD COLUMN IF NOT EXISTS answer_scale integer;
"""

REVERSE_SQL = """
ALTER TABLE public.user_onboarding_responses
    DROP COLUMN IF EXISTS answer_scale,
    DROP COLUMN IF EXISTS answer_body_map;

ALTER TABLE public.onboarding_questions
    DROP COLUMN IF EXISTS separator_text,
    DROP COLUMN IF EXISTS scale_min_label,
    DROP COLUMN IF EXISTS scale_max_label,
    DROP COLUMN IF EXISTS is_block_separator,
    DROP COLUMN IF EXISTS depends_on_question_id,
    DROP COLUMN IF EXISTS depends_on_answer,
    DROP COLUMN IF EXISTS block_order,
    DROP COLUMN IF EXISTS block_name;
"""

class Migration(migrations.Migration):
    dependencies = [
        ('onboarding', '0001_initial'),
    ]
    
    operations = [
        migrations.RunSQL(sql=SQL, reverse_sql=REVERSE_SQL),
    ]
    
    # Tell Django about the state changes so it doesn't try to create new migrations
    state_operations = [
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
    ]