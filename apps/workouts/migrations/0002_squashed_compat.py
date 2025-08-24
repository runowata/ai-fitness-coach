# Squashed migration to replace all workouts migrations 0002-0025
from django.db import migrations

class Migration(migrations.Migration):
    
    dependencies = [
        ('workouts', '0001_initial'),
    ]

    # Эта squashed-миграция ЗАМЕНЯЕТ все исторические миграции,
    # включая те, что применены в продакшене но отсутствуют в репо.
    # Операции no-op, т.к. прод уже содержит корректную схему.
    replaces = [
        ('workouts', '0002_alter_videoclip_type'),
        ('workouts', '0003_csvexercise_explainervideo_finalvideo_weeklylesson_and_more'),
        ('workouts', '0008_csvexercise_explainervideo'),
        ('workouts', '0010_weeklynotification'),
        ('workouts', '0011_safe_equipment_field_and_models'),
        ('workouts', '0012_add_duration_sec_field'),
        ('workouts', '0013_finalvideo_exercise_equipment_exercise_poster_image_and_more'),
        ('workouts', '0013_v2_schema'),
        ('workouts', '0014_clean_v1_legacy'),
        ('workouts', '0014_finalvideo_weeklylesson_and_more'),
        ('workouts', '0014_state_only'),
        ('workouts', '0015_add_v2_indexes'),
        ('workouts', '0015_merge_state_only_and_0012'),
        ('workouts', '0016_add_video_provider_fields'),
        ('workouts', '0016_v2_schema'),
        ('workouts', '0017_add_provider_constraints'),
        ('workouts', '0018_fix_unique_constraint_archetype_field'),
        ('workouts', '0019_remove_videoclip_provider_storage_consistency_and_more'),
        ('workouts', '0020_add_is_active_to_csvexercise'),
        ('workouts', '0021_sync_model_state'),
        ('workouts', '0022_add_contextual_video_fields'),
        ('workouts', '0023_alter_videoclip_exercise'),
        ('workouts', '0024_expand_exercise_name_lengths'),
        ('workouts', '0025_widen_charfields'),
    ]

    # НИКАКИХ операций — это совместительная-заглушка.
    operations = [
        migrations.RunPython(migrations.RunPython.noop, migrations.RunPython.noop)
    ]
    
    atomic = False