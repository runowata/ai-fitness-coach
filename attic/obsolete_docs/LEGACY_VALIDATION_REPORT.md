# COMPREHENSIVE LEGACY VALIDATION REPORT

## ОБЩАЯ СТАТИСТИКА
- Всего Python файлов: 645
- Синтаксических ошибок: 1
- Нарушений паттернов: 366
- Django ошибок: 0

## 🚨 СИНТАКСИЧЕСКИЕ ОШИБКИ
- /Users/alexbel/Desktop/Проекты/AI Fitness Coach/mass_exercise_refactor.py: Синтаксическая ошибка: строка 271: invalid syntax. Perhaps you forgot a comma?

## 🚨 НАРУШЕНИЯ LEGACY ПАТТЕРНОВ
### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/debug_video_system.py
- Строка 84: Запрещённая ссылка: CSVExercise.objects
- Строка 85: Запрещённая ссылка: CSVExercise.objects
- Строка 92: Запрещённая ссылка: CSVExercise.objects
- Строка 176: Запрещённая ссылка: CSVExercise.objects
- Строка 181: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/test_full_system.py
- Строка 33: Запрещённая ссылка: CSVExercise.objects
- Строка 34: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/test_r2_import_production.py
- Строка 67: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/mass_exercise_refactor.py
- Строка 26: Запрещённое поле: muscle_groups
- Строка 34: Запрещённая ссылка: CSVExercise(
- Строка 39: Запрещённая ссылка: CSVExercise(
- Строка 47: Запрещённая ссылка: CSVExercise.objects
- Строка 48: Запрещённая ссылка: CSVExercise.objects
- Строка 54: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 55: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 61: Запрещённая ссылка: CSVExercise(
- Строка 75: Запрещённая ссылка: # @admin.register(Exercise) - REMOVED in Phase 5.6
- Строка 86: Запрещённое поле: muscle_groups
- Строка 167: Запрещённое поле: muscle_groups
- Строка 168: Запрещённое поле: muscle_groups
- Строка 266: Запрещённая ссылка: CSVExercise.objects
- Строка 271: Запрещённая ссылка: CSVExercise.objects
- Строка 314: Запрещённая ссылка: CSVExercise.objects
- Строка 315: Запрещённое поле: muscle_groups
- Строка 320: Запрещённое поле: muscle_groups
- Строка 350: Запрещённая ссылка: CSVExercise(
- Строка 351: Запрещённая ссылка: CSVExercise(

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/comprehensive_legacy_validator.py
- Строка 29: Запрещённая ссылка: CSVExercise.objects
- Строка 30: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 31: Запрещённая ссылка: CSVExercise(
- Строка 32: Запрещённая ссылка: Exercise.Meta
- Строка 33: Запрещённая ссылка: # @admin.register(Exercise) - REMOVED in Phase 5.6
- Строка 36: Запрещённое поле: muscle_groups
- Строка 37: Запрещённое поле: equipment_needed
- Строка 183: Запрещённое поле: muscle_groups
- Строка 188: Запрещённое поле: muscle_groups
- Строка 190: Запрещённое поле: equipment_needed
- Строка 197: Запрещённое поле: alternatives

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/create_exercises.py
- Строка 118: Запрещённое поле: muscle_groups
- Строка 119: Запрещённая ссылка: CSVExercise.objects
- Строка 151: Запрещённая ссылка: CSVExercise.objects
- Строка 152: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/debug_video_system.py
- Строка 84: Запрещённая ссылка: CSVExercise.objects
- Строка 85: Запрещённая ссылка: CSVExercise.objects
- Строка 92: Запрещённая ссылка: CSVExercise.objects
- Строка 176: Запрещённая ссылка: CSVExercise.objects
- Строка 181: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/test_full_system.py
- Строка 33: Запрещённая ссылка: CSVExercise.objects
- Строка 34: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/test_r2_import_production.py
- Строка 67: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/mass_exercise_refactor.py
- Строка 26: Запрещённое поле: muscle_groups
- Строка 47: Запрещённая ссылка: CSVExercise.objects
- Строка 54: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 61: Запрещённая ссылка: CSVExercise(
- Строка 75: Запрещённая ссылка: # @admin.register(Exercise) - REMOVED in Phase 5.6
- Строка 86: Запрещённое поле: muscle_groups
- Строка 167: Запрещённое поле: muscle_groups
- Строка 168: Запрещённое поле: muscle_groups
- Строка 266: Запрещённая ссылка: CSVExercise.objects
- Строка 271: Запрещённая ссылка: CSVExercise.objects
- Строка 315: Запрещённое поле: muscle_groups
- Строка 320: Запрещённое поле: muscle_groups

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/comprehensive_legacy_validator.py
- Строка 32: Запрещённая ссылка: Exercise.Meta
- Строка 36: Запрещённое поле: muscle_groups
- Строка 37: Запрещённое поле: equipment_needed
- Строка 183: Запрещённое поле: muscle_groups
- Строка 188: Запрещённое поле: muscle_groups
- Строка 190: Запрещённое поле: equipment_needed
- Строка 197: Запрещённое поле: alternatives

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/create_exercises.py
- Строка 118: Запрещённое поле: muscle_groups

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/backup_before_refactor_20250828_205642/debug_video_system.py
- Строка 84: Запрещённая ссылка: CSVExercise.objects
- Строка 85: Запрещённая ссылка: CSVExercise.objects
- Строка 92: Запрещённая ссылка: CSVExercise.objects
- Строка 176: Запрещённая ссылка: CSVExercise.objects
- Строка 181: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/backup_before_refactor_20250828_205642/test_full_system.py
- Строка 33: Запрещённая ссылка: CSVExercise.objects
- Строка 34: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/backup_before_refactor_20250828_205642/test_r2_import_production.py
- Строка 67: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/backup_before_refactor_20250828_205642/mass_exercise_refactor.py
- Строка 26: Запрещённое поле: muscle_groups
- Строка 47: Запрещённая ссылка: CSVExercise.objects
- Строка 54: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 61: Запрещённая ссылка: CSVExercise(
- Строка 75: Запрещённая ссылка: # @admin.register(Exercise) - REMOVED in Phase 5.6
- Строка 86: Запрещённое поле: muscle_groups
- Строка 167: Запрещённое поле: muscle_groups
- Строка 168: Запрещённое поле: muscle_groups
- Строка 266: Запрещённая ссылка: CSVExercise.objects
- Строка 271: Запрещённая ссылка: CSVExercise.objects
- Строка 315: Запрещённое поле: muscle_groups
- Строка 320: Запрещённое поле: muscle_groups

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/backup_before_refactor_20250828_205642/comprehensive_legacy_validator.py
- Строка 32: Запрещённая ссылка: Exercise.Meta
- Строка 36: Запрещённое поле: muscle_groups
- Строка 37: Запрещённое поле: equipment_needed
- Строка 183: Запрещённое поле: muscle_groups
- Строка 188: Запрещённое поле: muscle_groups
- Строка 190: Запрещённое поле: equipment_needed
- Строка 197: Запрещённое поле: alternatives

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/backup_before_refactor_20250828_205642/create_exercises.py
- Строка 118: Запрещённое поле: muscle_groups

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/tests/test_playlist_v2.py
- Строка 111: Запрещённая ссылка: CSVExercise.objects
- Строка 144: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/tests/test_video_playlist_builder.py
- Строка 118: Запрещённая ссылка: CSVExercise.objects
- Строка 142: Запрещённая ссылка: CSVExercise.objects
- Строка 165: Запрещённая ссылка: CSVExercise.objects
- Строка 175: Запрещённая ссылка: CSVExercise.objects
- Строка 520: Запрещённая ссылка: CSVExercise.objects
- Строка 524: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/tests/test_catalog_build.py
- Строка 18: Запрещённая ссылка: CSVExercise.objects
- Строка 29: Запрещённая ссылка: CSVExercise.objects
- Строка 40: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/tests/test_video_playlist_deterministic.py
- Строка 25: Запрещённая ссылка: CSVExercise.objects
- Строка 34: Запрещённая ссылка: CSVExercise.objects
- Строка 257: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/tests/test_video_storage_adapters.py
- Строка 204: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/tests/test_ai_whitelist_enforcement.py
- Строка 22: Запрещённая ссылка: CSVExercise.objects
- Строка 30: Запрещённая ссылка: CSVExercise.objects
- Строка 38: Запрещённая ссылка: CSVExercise.objects
- Строка 46: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/tests/test_models.py
- Строка 69: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/tests/test_api_endpoints.py
- Строка 29: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/docs/diagnostics_v1/check_counts.py
- Строка 3: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/core/middleware.py
- Строка 181: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/core/management/commands/smoke_v2_ready.py
- Строка 56: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/core/management/commands/quick_data_check.py
- Строка 19: Запрещённая ссылка: CSVExercise.objects
- Строка 20: Запрещённая ссылка: CSVExercise.objects
- Строка 29: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/core/services/exercise_validation.py
- Строка 121: Запрещённая ссылка: CSVExercise.objects
- Строка 228: Запрещённое поле: muscle_groups
- Строка 231: Запрещённое поле: muscle_groups
- Строка 232: Запрещённое поле: muscle_groups
- Строка 233: Запрещённое поле: muscle_groups
- Строка 236: Запрещённое поле: muscle_groups
- Строка 238: Запрещённое поле: muscle_groups
- Строка 239: Запрещённое поле: muscle_groups
- Строка 240: Запрещённое поле: muscle_groups
- Строка 242: Запрещённое поле: muscle_groups
- Строка 245: Запрещённое поле: muscle_groups
- Строка 273: Запрещённое поле: muscle_groups
- Строка 275: Запрещённое поле: muscle_groups

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/catalog.py
- Строка 83: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/models.py
- Строка 359: Запрещённая ссылка: CSVExercise(

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/emergency_service.py
- Строка 84: Запрещённая ссылка: CSVExercise.objects
- Строка 93: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 100: Запрещённая ссылка: CSVExercise.objects
- Строка 109: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/video_services.py
- Строка 41: Запрещённая ссылка: CSVExercise.objects
- Строка 352: Запрещённая ссылка: CSVExercise.objects
- Строка 353: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 467: Запрещённая ссылка: CSVExercise.objects
- Строка 471: Запрещённая ссылка: CSVExercise.objects
- Строка 478: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/views.py
- Строка 54: Запрещённая ссылка: CSVExercise.objects
- Строка 68: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 158: Запрещённая ссылка: CSVExercise.objects
- Строка 159: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/migrations/0004_clean_exercise_model.py
- Строка 28: Запрещённое поле: muscle_groups

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/migrations/0001_initial.py
- Строка 340: Запрещённое поле: muscle_groups

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/management/commands/extract_exercises_from_r2.py
- Строка 206: Запрещённая ссылка: CSVExercise.objects
- Строка 212: Запрещённая ссылка: CSVExercise.objects
- Строка 245: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/management/commands/system_data_audit.py
- Строка 45: Запрещённая ссылка: CSVExercise.objects
- Строка 46: Запрещённая ссылка: CSVExercise.objects
- Строка 59: Запрещённая ссылка: CSVExercise.objects
- Строка 61: Запрещённая ссылка: CSVExercise.objects
- Строка 65: Запрещённая ссылка: CSVExercise.objects
- Строка 112: Запрещённая ссылка: CSVExercise.objects
- Строка 217: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/management/commands/check_catalog_integrity.py
- Строка 33: Запрещённая ссылка: CSVExercise.objects
- Строка 55: Запрещённая ссылка: CSVExercise.objects
- Строка 80: Запрещённая ссылка: CSVExercise.objects
- Строка 82: Запрещённая ссылка: CSVExercise.objects
- Строка 128: Запрещённая ссылка: CSVExercise.objects
- Строка 149: Запрещённая ссылка: CSVExercise.objects
- Строка 161: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/management/commands/import_exercises.py
- Строка 27: Запрещённая ссылка: CSVExercise.objects
- Строка 42: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/management/commands/sync_exercise_slugs.py
- Строка 105: Запрещённая ссылка: CSVExercise.objects
- Строка 230: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/management/commands/sync_r2_videos.py
- Строка 453: Запрещённая ссылка: CSVExercise.objects
- Строка 455: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 489: Запрещённая ссылка: CSVExercise.objects
- Строка 491: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/management/commands/check_exercise_mapping.py
- Строка 22: Запрещённая ссылка: CSVExercise.objects
- Строка 46: Запрещённая ссылка: CSVExercise.objects
- Строка 55: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 78: Запрещённая ссылка: CSVExercise.objects
- Строка 80: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/management/commands/bootstrap_v2_min.py
- Строка 34: Запрещённая ссылка: CSVExercise.objects
- Строка 107: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/management/commands/import_explainer_videos.py
- Строка 64: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/management/commands/bootstrap_from_videos.py
- Строка 87: Запрещённое поле: muscle_groups
- Строка 128: Запрещённое поле: muscle_groups

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/management/commands/import_exercises_v2.py
- Строка 89: Запрещённая ссылка: CSVExercise.objects
- Строка 148: Запрещённая ссылка: CSVExercise.objects
- Строка 210: Запрещённая ссылка: CSVExercise.objects
- Строка 211: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 269: Запрещённая ссылка: CSVExercise.objects
- Строка 270: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/management/commands/scan_r2_exercises.py
- Строка 269: Запрещённая ссылка: CSVExercise.objects
- Строка 292: Запрещённая ссылка: CSVExercise.objects
- Строка 323: Запрещённая ссылка: CSVExercise.objects
- Строка 324: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/management/commands/import_r2_exercises.py
- Строка 71: Запрещённая ссылка: CSVExercise.objects
- Строка 72: Запрещённая ссылка: CSVExercise.objects
- Строка 75: Запрещённая ссылка: CSVExercise.objects
- Строка 97: Запрещённая ссылка: CSVExercise.objects
- Строка 162: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/workouts/services/playlist_v2.py
- Строка 54: Запрещённая ссылка: CSVExercise.objects
- Строка 169: Запрещённая ссылка: CSVExercise.objects
- Строка 170: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/ai_integration/services.py
- Строка 521: Запрещённая ссылка: CSVExercise.objects
- Строка 533: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/ai_integration/fallback_service.py
- Строка 81: Запрещённое поле: muscle_groups
- Строка 121: Запрещённая ссылка: CSVExercise.objects
- Строка 170: Запрещённая ссылка: CSVExercise.objects
- Строка 179: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 197: Запрещённая ссылка: CSVExercise.objects
- Строка 262: Запрещённая ссылка: CSVExercise.objects
- Строка 371: Запрещённая ссылка: CSVExercise.objects
- Строка 373: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/backup_before_refactor_20250828_205642/apps/ai_integration/utils/exercise_whitelist.py
- Строка 27: Запрещённая ссылка: CSVExercise.objects
- Строка 53: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/tests/test_playlist_v2.py
- Строка 111: Запрещённая ссылка: CSVExercise.objects
- Строка 144: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/tests/test_video_playlist_builder.py
- Строка 118: Запрещённая ссылка: CSVExercise.objects
- Строка 142: Запрещённая ссылка: CSVExercise.objects
- Строка 165: Запрещённая ссылка: CSVExercise.objects
- Строка 175: Запрещённая ссылка: CSVExercise.objects
- Строка 520: Запрещённая ссылка: CSVExercise.objects
- Строка 524: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/tests/test_catalog_build.py
- Строка 18: Запрещённая ссылка: CSVExercise.objects
- Строка 29: Запрещённая ссылка: CSVExercise.objects
- Строка 40: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/tests/test_services.py
- Строка 34: Запрещённая ссылка: CSVExercise.objects
- Строка 318: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/tests/test_video_playlist_deterministic.py
- Строка 25: Запрещённая ссылка: CSVExercise.objects
- Строка 34: Запрещённая ссылка: CSVExercise.objects
- Строка 257: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/tests/test_e2e_user_flow.py
- Строка 436: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/tests/test_video_storage_adapters.py
- Строка 204: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/tests/test_ai_whitelist_enforcement.py
- Строка 22: Запрещённая ссылка: CSVExercise.objects
- Строка 30: Запрещённая ссылка: CSVExercise.objects
- Строка 38: Запрещённая ссылка: CSVExercise.objects
- Строка 46: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/tests/test_models.py
- Строка 51: Запрещённая ссылка: CSVExercise.objects
- Строка 69: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/tests/test_e2e.py
- Строка 45: Запрещённая ссылка: CSVExercise.objects
- Строка 288: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/tests/test_api_endpoints.py
- Строка 29: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/docs/diagnostics_v1/check_counts.py
- Строка 3: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/dev_tools/management_commands/debug_workout_video.py
- Строка 66: Запрещённая ссылка: CSVExercise.objects
- Строка 69: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/core/middleware.py
- Строка 181: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/core/views.py
- Строка 92: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/core/management/commands/smoke_v2_ready.py
- Строка 56: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/core/management/commands/quick_data_check.py
- Строка 19: Запрещённая ссылка: CSVExercise.objects
- Строка 20: Запрещённая ссылка: CSVExercise.objects
- Строка 29: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/core/services/exercise_validation.py
- Строка 121: Запрещённая ссылка: CSVExercise.objects
- Строка 228: Запрещённое поле: muscle_groups
- Строка 231: Запрещённое поле: muscle_groups
- Строка 232: Запрещённое поле: muscle_groups
- Строка 233: Запрещённое поле: muscle_groups
- Строка 236: Запрещённое поле: muscle_groups
- Строка 238: Запрещённое поле: muscle_groups
- Строка 239: Запрещённое поле: muscle_groups
- Строка 240: Запрещённое поле: muscle_groups
- Строка 242: Запрещённое поле: muscle_groups
- Строка 245: Запрещённое поле: muscle_groups
- Строка 273: Запрещённое поле: muscle_groups
- Строка 275: Запрещённое поле: muscle_groups

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/catalog.py
- Строка 83: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/models.py
- Строка 359: Запрещённая ссылка: CSVExercise(

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/emergency_service.py
- Строка 84: Запрещённая ссылка: CSVExercise.objects
- Строка 93: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 100: Запрещённая ссылка: CSVExercise.objects
- Строка 109: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/video_services.py
- Строка 41: Запрещённая ссылка: CSVExercise.objects
- Строка 352: Запрещённая ссылка: CSVExercise.objects
- Строка 353: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 467: Запрещённая ссылка: CSVExercise.objects
- Строка 471: Запрещённая ссылка: CSVExercise.objects
- Строка 478: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/views.py
- Строка 54: Запрещённая ссылка: CSVExercise.objects
- Строка 68: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 158: Запрещённая ссылка: CSVExercise.objects
- Строка 159: Запрещённая ссылка: CSVExercise.objects
- Строка 199: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/migrations/0004_clean_exercise_model.py
- Строка 28: Запрещённое поле: muscle_groups

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/migrations/0001_initial.py
- Строка 340: Запрещённое поле: muscle_groups

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/management/commands/extract_exercises_from_r2.py
- Строка 206: Запрещённая ссылка: CSVExercise.objects
- Строка 212: Запрещённая ссылка: CSVExercise.objects
- Строка 245: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/management/commands/system_data_audit.py
- Строка 45: Запрещённая ссылка: CSVExercise.objects
- Строка 46: Запрещённая ссылка: CSVExercise.objects
- Строка 59: Запрещённая ссылка: CSVExercise.objects
- Строка 61: Запрещённая ссылка: CSVExercise.objects
- Строка 65: Запрещённая ссылка: CSVExercise.objects
- Строка 112: Запрещённая ссылка: CSVExercise.objects
- Строка 217: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/management/commands/check_catalog_integrity.py
- Строка 33: Запрещённая ссылка: CSVExercise.objects
- Строка 55: Запрещённая ссылка: CSVExercise.objects
- Строка 80: Запрещённая ссылка: CSVExercise.objects
- Строка 82: Запрещённая ссылка: CSVExercise.objects
- Строка 128: Запрещённая ссылка: CSVExercise.objects
- Строка 149: Запрещённая ссылка: CSVExercise.objects
- Строка 161: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/management/commands/import_exercises.py
- Строка 27: Запрещённая ссылка: CSVExercise.objects
- Строка 42: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/management/commands/sync_exercise_slugs.py
- Строка 105: Запрещённая ссылка: CSVExercise.objects
- Строка 230: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/management/commands/sync_r2_videos.py
- Строка 453: Запрещённая ссылка: CSVExercise.objects
- Строка 455: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 489: Запрещённая ссылка: CSVExercise.objects
- Строка 491: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/management/commands/check_exercise_mapping.py
- Строка 22: Запрещённая ссылка: CSVExercise.objects
- Строка 46: Запрещённая ссылка: CSVExercise.objects
- Строка 55: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 78: Запрещённая ссылка: CSVExercise.objects
- Строка 80: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/management/commands/bootstrap_v2_min.py
- Строка 34: Запрещённая ссылка: CSVExercise.objects
- Строка 107: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/management/commands/import_explainer_videos.py
- Строка 64: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/management/commands/create_placeholder_videos.py
- Строка 20: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/management/commands/bootstrap_from_videos.py
- Строка 87: Запрещённое поле: muscle_groups
- Строка 128: Запрещённое поле: muscle_groups
- Строка 226: Запрещённая ссылка: CSVExercise.objects
- Строка 231: Запрещённая ссылка: CSVExercise.objects
- Строка 239: Запрещённая ссылка: CSVExercise.objects
- Строка 253: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/management/commands/import_exercises_v2.py
- Строка 89: Запрещённая ссылка: CSVExercise.objects
- Строка 148: Запрещённая ссылка: CSVExercise.objects
- Строка 210: Запрещённая ссылка: CSVExercise.objects
- Строка 211: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 269: Запрещённая ссылка: CSVExercise.objects
- Строка 270: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/management/commands/scan_r2_exercises.py
- Строка 269: Запрещённая ссылка: CSVExercise.objects
- Строка 292: Запрещённая ссылка: CSVExercise.objects
- Строка 323: Запрещённая ссылка: CSVExercise.objects
- Строка 324: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/management/commands/import_r2_exercises.py
- Строка 71: Запрещённая ссылка: CSVExercise.objects
- Строка 72: Запрещённая ссылка: CSVExercise.objects
- Строка 75: Запрещённая ссылка: CSVExercise.objects
- Строка 97: Запрещённая ссылка: CSVExercise.objects
- Строка 162: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/management/commands/create_basic_exercises.py
- Строка 94: Запрещённая ссылка: CSVExercise.objects
- Строка 101: Запрещённая ссылка: CSVExercise.objects
- Строка 115: Запрещённая ссылка: CSVExercise.objects
- Строка 122: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/workouts/services/playlist_v2.py
- Строка 54: Запрещённая ссылка: CSVExercise.objects
- Строка 169: Запрещённая ссылка: CSVExercise.objects
- Строка 170: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/ai_integration/services.py
- Строка 521: Запрещённая ссылка: CSVExercise.objects
- Строка 533: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/ai_integration/fallback_service.py
- Строка 81: Запрещённое поле: muscle_groups
- Строка 121: Запрещённая ссылка: CSVExercise.objects
- Строка 170: Запрещённая ссылка: CSVExercise.objects
- Строка 179: Запрещённая ссылка: CSVExercise.DoesNotExist
- Строка 197: Запрещённая ссылка: CSVExercise.objects
- Строка 262: Запрещённая ссылка: CSVExercise.objects
- Строка 371: Запрещённая ссылка: CSVExercise.objects
- Строка 373: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/ai_integration/utils/exercise_whitelist.py
- Строка 27: Запрещённая ссылка: CSVExercise.objects
- Строка 53: Запрещённая ссылка: CSVExercise.objects

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/content/management/commands/import_media.py
- Строка 144: Запрещённая ссылка: CSVExercise.objects
- Строка 147: Запрещённая ссылка: CSVExercise.DoesNotExist

### /Users/alexbel/Desktop/Проекты/AI Fitness Coach/apps/onboarding/views.py
- Строка 1053: Запрещённая ссылка: CSVExercise.objects

## ❌ ВАЛИДАЦИЯ НЕ ПРОЙДЕНА
Найдено 367 критических проблем, требующих исправления.
