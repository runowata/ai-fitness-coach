# Движение пользователя и данных (v1)

## 1. Онбординг → сбор данных
- Вьюхи/шаблоны: apps/onboarding/views.py, templates/onboarding/*
- Модели: apps/onboarding/models.py, apps/users/models.py
- Сервис: apps/onboarding/services.py::OnboardingDataProcessor.collect_user_data

## 2. Генерация плана ИИ
- Клиент/промпты: apps/ai_integration/ai_client*.py, apps/ai_integration/prompt_manager_v2.py
- Схемы: apps/ai_integration/schemas.py, apps/ai_integration/schemas_json.py
- Белый список упражнений: apps/ai_integration/utils/exercise_whitelist.py
- Сервис: apps/ai_integration/services.py::WorkoutPlanGenerator / WorkoutPlanValidator
- Результат в БД: WorkoutPlan(plan_data, ai_analysis)

## 3. Каталог упражнений/медиа
- CSVExercise (импорт: apps/workouts/management/commands/import_exercises.py) из data/clean/exercises.csv
- VideoClip (связь c CSVExercise, archetype, r2_kind, provider, duration_seconds, r2_file/path)
- Типы клипов: apps/workouts/constants.py::VideoKind
- Валидация медиатеки: apps/workouts/management/commands/audit_video_clips.py
- Покрытие упражнений: apps/core/services/exercise_validation.py

## 4. Плейлисты и уроки
- Генерация дневного плейлиста: apps/workouts/services/playlist_v2.py, apps/workouts/video_services.py
- Требуемые клипы на упражнение: REQUIRED_VIDEO_KINDS_PLAYLIST = [TECHNIQUE, INSTRUCTION]
- Опциональные вставки: INTRO/MID_WORKOUT/MOTIVATIONAL_BREAK/... (см. constants.py)
- Еженедельные и финальные тексты: WeeklyLesson / FinalVideo (импорт YAML: import_weekly_and_final.py)

## 5. Фронтенд и обратная связь
- Превью/подтверждение плана: templates/onboarding/plan_preview*.html, plan_confirmation.html
- Дневная тренировка и фидбэк: templates/workouts/daily_workout.html → /workouts/complete/<id>/
- Недельный фидбэк: templates/workouts/weekly_feedback.html
- История/план: templates/workouts/history.html

## 6. Что из анкеты реально влияет
- biological_sex — **не влияет**
- fitness_level — есть в моделях, но **не используется** как фильтр
- equipment_list — ai_tags сохраняются, но **не используются** как фильтр
- Ключевой драйвер — JSON-план ИИ (exercise_slug) + покрытие видео (TECHNIQUE + INSTRUCTION)

## 7. Где что лежит
- CSV: data/clean/exercises.csv (id, name_ru/en, level, exercise_type, muscle_group, ai_tags, is_active)
- Медиа R2: VideoClip.r2_file / r2_kind / provider (проверяется audit_video_clips)
- БД: WorkoutPlan / DailyWorkout / CSVExercise / VideoClip / WeeklyLesson / FinalVideo

## 8. Видео «от тренеров»
- Ежедневные: VideoClip.r2_kind = INTRO / MID_WORKOUT / MOTIVATIONAL_BREAK / CONTEXTUAL_INTRO/OUTRO
- Еженедельные: WeeklyLesson (пока текст) → можно добавить VideoKind.WEEKLY
- Финальные: FinalVideo (текст) → можно добавить VideoKind.CLOSING
- Награда 2 недели: категории нет → добавить VideoKind.FORTNIGHT_REWARD

## 9. Обратная связь
- Дневная: DailyWorkout (perceived_exertion, mood, feedback_note, completed_at)
- Недельная: отдельный UI (weekly_feedback.html)

---
_Git commit: 76f5aa481baef7c28bded6eed19a6e0a29145555_
_Date: 2025-08-26 17:58:40_