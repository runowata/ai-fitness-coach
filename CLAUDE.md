# AI Fitness Coach - Claude Context

## Project Overview
AI Fitness Coach - это веб-приложение для персонализированных тренировок, созданное специально для мужчин-геев. Приложение комбинирует фитнес-тренировки с заданиями на развитие уверенности и наградным эротическим контентом.

## Architecture
- **Backend:** Django 5.x + PostgreSQL
- **Frontend:** Server-side rendering + Bootstrap 5
- **Storage:** AWS S3 для медиа-файлов
- **AI:** OpenAI GPT-4 или Claude для генерации планов
- **Deployment:** Render.com

## Key Features Implemented

### 1. User Authentication & Profiles
- Кастомная модель пользователя с проверкой 18+
- UserProfile с XP системой и достижениями
- Выбор часового пояса и системы измерений
- 2FA support (TOTP)

### 2. Onboarding Flow
- Пошаговый опросник (`OnboardingQuestion`/`AnswerOption`)
- Мотивационные карточки после ответов
- Выбор архетипа тренера (Бро/Сержант/Интеллектуал)
- AI-генерация персонального плана тренировок

### 3. Workout System
- `Exercise` модели с альтернативами для замены
- `WorkoutPlan` с еженедельной адаптацией
- `DailyWorkout` с видео-плейлистами
- Система замены упражнений одним кликом
- Микро-обратная связь с эмодзи рейтингом

### 4. Video & Media Management
- `VideoClip` модели для разных типов контента
- `MediaAsset` для управления S3 файлами
- Автоматическая сборка плейлистов по архетипу
- CDN интеграция через CloudFront

### 5. Achievement & Reward System
- `Achievement` модели с различными триггерами
- XP система с уровнями (100 XP = 1 level)
- Автоматическая проверка достижений после тренировок
- Разблокировка глав историй через `UserStoryAccess`

### 6. Story Content System
- `Story` и `StoryChapter` для эротического контента
- Система доступа на основе достижений
- Трекинг прочтений и статистика

### 7. Notification System
- Email уведомления через Celery tasks
- Ежедневные напоминания о тренировках
- Уведомления о достижениях
- Еженедельные отчеты о прогрессе

## AI Integration

### Workout Plan Generation
- **Prompt:** `prompts/workout_plan_generation.txt`
- **Input:** Данные пользователя из онбординга
- **Output:** JSON структура с планом на 4-8 недель
- **Service:** `WorkoutPlanGenerator.generate_plan()`

### Weekly Adaptation
- **Prompt:** `prompts/weekly_adaptation.txt`
- **Input:** Обратная связь пользователя за неделю
- **Output:** Модификации для следующей недели
- **Service:** `WorkoutPlanGenerator.adapt_weekly_plan()`

## Database Models Structure

### Core Models
- `User` (кастомная модель с timezone/measurement preferences)
- `UserProfile` (XP, уровень, статистика, настройки)
- `Exercise` (упражнения с альтернативами)
- `WorkoutPlan` (AI-сгенерированные планы)
- `DailyWorkout` (ежедневные тренировки)

### Content Models
- `VideoClip` (видео по типам и архетипам)
- `MediaAsset` (файловое хранилище)
- `Story`/`StoryChapter` (эротический контент)
- `UserStoryAccess` (доступ к главам)

### Gamification
- `Achievement` (достижения)
- `UserAchievement` (разблокированные достижения)
- `XPTransaction` (история XP)
- `DailyProgress` (ежедневная статистика)

## Key Services

### `VideoPlaylistBuilder`
Собирает видео-плейлисты для тренировок:
1. Техника выполнения (mod1)
2. Инструктаж (архетип + random model)
3. 2-3 напоминания (архетип)
4. Иногда видео ошибок (30% вероятность)

### `AchievementChecker`
Проверяет достижения после каждой тренировки:
- workout_count, streak_days, xp_earned
- plan_completed, perfect_week, confidence_tasks

### `WorkoutCompletionService`
Обрабатывает завершение тренировки:
- Обновляет статистику пользователя
- Начисляет XP (50-125 очков)
- Проверяет достижения
- Обновляет стрики

## Media File Structure
```
/videos/exercises/{slug}_technique_{model}.mp4
/videos/exercises/{slug}_mistake_{model}.mp4  
/videos/instructions/{slug}_instruction_{archetype}_{model}.mp4
/videos/reminders/{slug}_reminder_{archetype}_{number}.mp4
/videos/motivation/weekly_{archetype}_week{number}.mp4
/videos/motivation/final_{archetype}.mp4
/images/cards/card_{category}_{number}.jpg
/images/avatars/{archetype}_avatar_{number}.jpg
/images/stories/{story_slug}_cover.jpg
```

## Deployment Commands

### Initial Setup
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata fixtures/*.json
python manage.py createsuperuser
```

### Media Import
```bash
python manage.py import_media /path/to/media --dry-run
python manage.py import_media /path/to/media --category exercise_technique
```

## Testing
- Unit tests in `tests/test_models.py`
- Run with: `pytest`
- Coverage target: ≥80%

## Key URLs
- `/` - Homepage
- `/users/dashboard/` - Main dashboard
- `/onboarding/start/` - Onboarding flow
- `/workouts/daily/<id>/` - Daily workout
- `/content/stories/` - Story library
- `/admin/` - Django admin

## Settings Notes
- `AUTH_USER_MODEL = 'users.User'`
- Timezone default: `Europe/Zurich`
- Email backend configured for notifications
- S3 storage for production media
- Rate limiting on workout completion

## Future Enhancements
- Progressive Web App (PWA)
- Mobile push notifications
- Advanced analytics dashboard
- Social features (friends, leaderboards)
- Wearable device integration