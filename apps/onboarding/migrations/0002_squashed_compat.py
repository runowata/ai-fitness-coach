# Squashed migration to replace problematic legacy migrations 0002-0008
from django.db import migrations

class Migration(migrations.Migration):
    # ВАЖНО: зависит от 0001_initial
    dependencies = [
        ('onboarding', '0001_initial'),
    ]

    # Эта squashed-миграция ЗАМЕНЯЕТ весь легаси-хвост,
    # но не выполняет никаких операций (no-op), т.к. прод уже корректен.
    replaces = [
        ('onboarding', '0002_conditional_schema_migration'),
        ('onboarding', '0003_motivationalcard_answer_option_and_more'),
        ('onboarding', '0004_motivationalcard_image'),
        ('onboarding', '0005_motivationalcard_path_alter_motivationalcard_image_and_more'),
        ('onboarding', '0006_populate_path_from_image_url'),
        ('onboarding', '0007_backfill_and_defaults'),
        ('onboarding', '0008_enforce_unique_pair_when_set'),
    ]

    # НИКАКИХ операций — это совместительная-заглушка.
    operations = []