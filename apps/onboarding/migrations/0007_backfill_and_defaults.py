from django.db import migrations

def backfill_defaults(apps, schema_editor):
    """Backfill NULL values and set defaults (database-agnostic)"""
    with schema_editor.connection.cursor() as cursor:
        # Backfill NULLs
        cursor.execute("""
            UPDATE onboarding_questions
            SET block_order = 1
            WHERE block_order IS NULL;
        """)
        cursor.execute("""
            UPDATE onboarding_questions
            SET is_block_separator = 0
            WHERE is_block_separator IS NULL;
        """)
        
        # Set defaults only for PostgreSQL
        if schema_editor.connection.vendor == 'postgresql':
            cursor.execute("ALTER TABLE onboarding_questions ALTER COLUMN block_order SET DEFAULT 1;")
            cursor.execute("ALTER TABLE onboarding_questions ALTER COLUMN is_block_separator SET DEFAULT false;")

class Migration(migrations.Migration):
    dependencies = [
        ('onboarding', '0006_populate_path_from_image_url'),
    ]
    atomic = False  # allow chunked updates if needed

    operations = [
        migrations.RunPython(
            code=backfill_defaults,
            reverse_code=migrations.RunPython.noop,
        ),
    ]