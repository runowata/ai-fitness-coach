# apps/onboarding/migrations/0002b_backfill_and_defaults.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('onboarding', '0006_populate_path_from_image_url'),
    ]
    atomic = False  # allow chunked updates if needed

    operations = [
        # Backfill NULLs
        migrations.RunSQL(
            """
            UPDATE public.onboarding_questions
            SET block_order = 1
            WHERE block_order IS NULL;
            """,
            reverse_sql=None,
        ),
        migrations.RunSQL(
            """
            UPDATE public.onboarding_questions
            SET is_block_separator = false
            WHERE is_block_separator IS NULL;
            """,
            reverse_sql=None,
        ),
        # Establish lightweight defaults for new inserts (no NOT NULL here)
        migrations.RunSQL(
            "ALTER TABLE public.onboarding_questions ALTER COLUMN block_order SET DEFAULT 1;",
            reverse_sql="ALTER TABLE public.onboarding_questions ALTER COLUMN block_order DROP DEFAULT;",
        ),
        migrations.RunSQL(
            "ALTER TABLE public.onboarding_questions ALTER COLUMN is_block_separator SET DEFAULT false;",
            reverse_sql="ALTER TABLE public.onboarding_questions ALTER COLUMN is_block_separator DROP DEFAULT;",
        ),
    ]