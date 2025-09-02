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

    def fix_question_5(apps, schema_editor):
        """Fix question 5 to display answer options instead of block separator"""
        OnboardingQuestion = apps.get_model("onboarding", "OnboardingQuestion")
        AnswerOption = apps.get_model("onboarding", "AnswerOption")

        # 1) Find question by reliable key
        q = OnboardingQuestion.objects.filter(order=5).first()
        if not q:
            # Nothing to fix - exit silently (idempotent)
            return

        # 2) If it's a separator - convert to normal question with single choice
        mutated = False
        if getattr(q, "is_block_separator", False):
            q.is_block_separator = False
            if hasattr(q, "separator_text"):
                q.separator_text = ""
            # Set correct question type
            if hasattr(q, "question_type"):
                q.question_type = "single_choice"
            mutated = True

        # 3) Ensure question has answer options
        has_options = AnswerOption.objects.filter(question=q).exists()
        if not has_options:
            # Basic safe set of options
            defaults = [
                {"option_text": "Я понял, теперь я спокоен", "option_value": "understood_calm", "order": 1},
                {"option_text": "Понятно, продолжим", "option_value": "understood_continue", "order": 2}, 
                {"option_text": "Хорошо, я буду честен", "option_value": "understood_honest", "order": 3},
            ]
            
            for item in defaults:
                ao_kwargs = {"question": q, "option_text": item["option_text"]}
                ao_defaults = {
                    "option_value": item["option_value"],
                    "order": item["order"]
                }
                AnswerOption.objects.get_or_create(**ao_kwargs, defaults=ao_defaults)
            mutated = True

        if mutated:
            # Save question changes if any
            save_fields = []
            for f in ["is_block_separator", "separator_text", "question_type"]:
                if hasattr(q, f):
                    save_fields.append(f)
            if save_fields:
                q.save(update_fields=save_fields)

    # Операции: no-op для истории + data fix для продакшена
    operations = [
        migrations.RunPython(migrations.RunPython.noop, migrations.RunPython.noop),
        migrations.RunPython(fix_question_5, migrations.RunPython.noop),
    ]