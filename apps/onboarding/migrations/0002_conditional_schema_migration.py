import django.db.models.deletion
from django.db import migrations, models

def safe_add_columns(apps, schema_editor):
    """Safely add columns with cross-database compatibility"""
    Question = apps.get_model('onboarding', 'OnboardingQuestion')
    Response = apps.get_model('onboarding', 'UserOnboardingResponse')
    question_table = Question._meta.db_table
    response_table = Response._meta.db_table
    
    # Define columns to add
    columns = [
        (question_table, "block_name", "varchar(100)"),
        (question_table, "block_order", "integer"),
        (question_table, "depends_on_answer", "varchar(100)"),
        (question_table, "depends_on_question_id", "integer"),
        (question_table, "is_block_separator", "boolean"),
        (question_table, "scale_max_label", "varchar(50)"),
        (question_table, "scale_min_label", "varchar(50)"),
        (question_table, "separator_text", "text"),
        (response_table, "answer_body_map", "jsonb"),
        (response_table, "answer_scale", "integer"),
    ]
    
    with schema_editor.connection.cursor() as cursor:
        for table, column, sql_type in columns:
            # Check if column exists (cross-database compatible)
            if schema_editor.connection.vendor == 'postgresql':
                cursor.execute("""
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = %s
                      AND column_name = %s
                """, [table, column])
            else:  # SQLite
                cursor.execute("""
                    SELECT 1
                    FROM pragma_table_info(?)
                    WHERE name = ?
                """, [table, column])
            
            exists = cursor.fetchone() is not None
            if exists:
                continue
                
            # Add column safely
            if schema_editor.connection.vendor == 'postgresql':
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {sql_type};')
            else:  # SQLite doesn't support jsonb, use json
                if sql_type == 'jsonb':
                    sql_type = 'json'
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {sql_type};')

class Migration(migrations.Migration):
    dependencies = [
        ('onboarding', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(
            code=safe_add_columns,
            reverse_code=migrations.RunPython.noop,
        ),
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