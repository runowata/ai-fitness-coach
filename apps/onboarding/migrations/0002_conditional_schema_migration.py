# Generated to conditionally apply schema changes based on current database state

import django.db.models.deletion
from django.db import migrations, models, connection


def check_and_add_columns(apps, schema_editor):
    """Conditionally add columns only if they don't exist"""
    
    def column_exists(table_name, column_name):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = %s AND column_name = %s
                );
            """, [table_name, column_name])
            return cursor.fetchone()[0]
    
    # Get model classes
    OnboardingQuestion = apps.get_model('onboarding', 'OnboardingQuestion')
    UserOnboardingResponse = apps.get_model('onboarding', 'UserOnboardingResponse')
    
    # Add columns only if they don't exist
    columns_to_add = [
        ('onboarding_onboardingquestion', 'block_name', 'VARCHAR(100)'),
        ('onboarding_onboardingquestion', 'block_order', 'INTEGER DEFAULT 1'),
        ('onboarding_onboardingquestion', 'depends_on_answer', 'VARCHAR(100)'),
        ('onboarding_onboardingquestion', 'depends_on_question_id', 'INTEGER'),
        ('onboarding_onboardingquestion', 'is_block_separator', 'BOOLEAN DEFAULT false'),
        ('onboarding_onboardingquestion', 'scale_max_label', 'VARCHAR(50)'),
        ('onboarding_onboardingquestion', 'scale_min_label', 'VARCHAR(50)'),
        ('onboarding_onboardingquestion', 'separator_text', 'TEXT'),
        ('onboarding_useronboardingresponse', 'answer_body_map', 'JSONB'),
        ('onboarding_useronboardingresponse', 'answer_scale', 'INTEGER'),
    ]
    
    with connection.cursor() as cursor:
        for table, column, definition in columns_to_add:
            if not column_exists(table, column):
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition};')
                print(f"Added column {column} to {table}")
            else:
                print(f"Column {column} already exists in {table}")
    
    # Update question_type choices if needed
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE onboarding_onboardingquestion 
            SET question_type = question_type 
            WHERE question_type IN ('single_choice', 'multiple_choice', 'number', 'text', 'scale', 'body_map');
        """)


def reverse_migration(apps, schema_editor):
    """Reverse the migration - remove added columns"""
    
    columns_to_remove = [
        ('onboarding_onboardingquestion', 'block_name'),
        ('onboarding_onboardingquestion', 'block_order'),
        ('onboarding_onboardingquestion', 'depends_on_answer'),
        ('onboarding_onboardingquestion', 'depends_on_question_id'),
        ('onboarding_onboardingquestion', 'is_block_separator'),
        ('onboarding_onboardingquestion', 'scale_max_label'),
        ('onboarding_onboardingquestion', 'scale_min_label'),
        ('onboarding_onboardingquestion', 'separator_text'),
        ('onboarding_useronboardingresponse', 'answer_body_map'),
        ('onboarding_useronboardingresponse', 'answer_scale'),
    ]
    
    with connection.cursor() as cursor:
        for table, column in columns_to_remove:
            try:
                cursor.execute(f'ALTER TABLE {table} DROP COLUMN {column};')
            except Exception:
                pass  # Column might not exist


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(check_and_add_columns, reverse_migration),
    ]