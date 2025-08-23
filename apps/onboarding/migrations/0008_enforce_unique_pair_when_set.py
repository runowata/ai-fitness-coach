# apps/onboarding/migrations/0006_enforce_unique_pair_when_set.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('onboarding', '0007_backfill_and_defaults'),
    ]
    operations = [
        migrations.RunSQL(
            sql=("""
                CREATE UNIQUE INDEX IF NOT EXISTS uq_mcard_q_a_notnull
                ON motivational_cards (question_id, answer_option_id)
                WHERE question_id IS NOT NULL AND answer_option_id IS NOT NULL;
            """),
            reverse_sql=("DROP INDEX IF EXISTS uq_mcard_q_a_notnull;"),
        ),
    ]