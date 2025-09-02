# AI Fitness Coach - Deployment Guide

## ✅ Все критичные разрывы устранены!

### Исправленные проблемы:

1. **✅ OnboardingQuestion.is_active** - поле есть, обновлены фикстуры
2. **✅ Недостающие шаблоны** - созданы все required шаблоны:
   - `onboarding/plan_preview.html`
   - `onboarding/error.html`
   - `content/stories_list.html`
   - `content/story_detail.html`
   - `content/read_chapter.html`
   - `core/about.html`
   - `core/help.html`
   - `core/privacy.html`
   - `core/terms.html`
   - `users/profile_settings.html`

3. **✅ Дублирование сервисов** - создана функция `create_workout_plan_from_onboarding()`
4. **✅ Образцы медиа** - созданы фикстуры `video_clips.json` и `achievements.json` с рабочими URL
5. **✅ Команда import_media** - улучшена с детальным парсингом файлов
6. **✅ End-to-end тест** - полный тест пользовательского journey
7. **✅ Опечатка form.valid()** - исправлена в `users/views.py`
8. **✅ Pre-commit конфиг** - добавлен `.pre-commit-config.yaml`
9. **✅ Версии пакетов** - закреплены в `requirements.txt`

## 🚀 Команды для запуска:

### 1. Базовая настройка
```bash
cd "AI Fitness Coach"

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Настройка базы данных
```bash
# Копирование настроек
cp .env.example .env
# Отредактируйте .env файл с вашими настройками

# Миграции
python manage.py makemigrations
python manage.py migrate

# Загрузка тестовых данных
python manage.py loaddata fixtures/exercises.json
python manage.py loaddata fixtures/onboarding_questions.json
python manage.py loaddata fixtures/motivational_cards.json
python manage.py loaddata fixtures/stories.json
python manage.py loaddata fixtures/video_clips.json
python manage.py loaddata fixtures/achievements.json

# Создание админа
python manage.py createsuperuser
```

### 3. Запуск сервера
```bash
# Development
python manage.py runserver

# Production (с Gunicorn)
gunicorn config.wsgi:application
```

## 🧪 Тестирование

```bash
# Запуск всех тестов
pytest

# Запуск end-to-end теста
pytest tests/test_e2e.py::EndToEndUserFlowTest::test_complete_user_journey

# Проверка покрытия
pytest --cov=apps
```

## 📁 Загрузка медиа-файлов

```bash
# Dry run для проверки
python manage.py import_media /path/to/media --dry-run

# Загрузка конкретной категории
python manage.py import_media /path/to/videos --category exercise_technique

# Полная загрузка
python manage.py import_media /path/to/media
```

## 🎯 End-to-End User Journey (100% рабочий)

1. **Регистрация** → `POST /users/register/`
2. **Онбординг** → `GET /onboarding/start/`
3. **Вопросы** → `POST /onboarding/answer/{id}/`
4. **Выбор архетипа** → `POST /onboarding/archetype/`
5. **Генерация плана** → `GET /onboarding/generate/`
6. **Дашборд** → `GET /users/dashboard/`
7. **Тренировка** → `GET /workouts/daily/{id}/`
8. **Завершение** → `POST /workouts/complete/{id}/`
9. **Достижения** → автоматически
10. **Истории** → `GET /content/stories/`
11. **Чтение** → `GET /content/stories/{slug}/chapter/{num}/`

## 🔧 Быстрое локальное развертывание

```bash
# Клонирование
git clone <repo-url>
cd "AI Fitness Coach"

# Автоматическая настройка
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata fixtures/*.json
python manage.py createsuperuser
python manage.py runserver
```

Откройте http://127.0.0.1:8000/ - проект полностью готов к использованию!

## 🏭 Production Deployment (Render.com)

1. Пушите код в GitHub
2. Подключите репозиторий к Render.com
3. Render автоматически использует `render.yaml`
4. Настройте переменные окружения в Render Dashboard
5. Deployment запустится автоматически

## 📊 Доступные фикстуры

- `exercises.json` - 5 базовых упражнений
- `onboarding_questions.json` - **15 расширенных вопросов** для детального профиля пользователя
- `motivational_cards.json` - 5 мотивационных карточек
- `stories.json` - 3 истории с главами
- `video_clips.json` - 15 работающих видеороликов с Google Cloud
- `achievements.json` - 5 достижений с наградами

## 🧠 Расширенный ИИ-онбординг

Новая система онбординга собирает **15 ключевых параметров** для создания максимально персонализированного плана:

### Базовые данные:
1. **Основная цель** - похудение, набор массы, выносливость, уверенность, подготовка к событию
2. **Возраст, рост, вес** - для расчета нагрузок
3. **Опыт тренировок** - новичок, средний, продвинутый

### Планирование тренировок:
4. **Дни в неделю** - от 2-3 до ежедневных тренировок
5. **Время тренировки** - 20-30 мин до 60+ минут
6. **Время дня** - утро, день, вечер, поздний вечер
7. **Доступное оборудование** - от веса тела до полного зала

### Здоровье и ограничения:
8. **Проблемы со здоровьем** - спина, колени, плечи, сердце
9. **Недавняя активность** - от сидячего образа до активного
10. **Предпочтения упражнений** - силовые, кардио, функциональные, йога, танцы

### Психологический профиль:
11. **Комфорт в зале** - от очень некомфортно до уверенно
12. **Стиль мотивации** - визуальные результаты, производительность, социальное одобрение, самочувствие
13. **Длительность программы** - 4, 6, 8 или 12 недель

### ИИ использует эти данные для:
- **Персонализации упражнений** под доступное оборудование и ограничения
- **Адаптации интенсивности** под опыт и недавнюю активность
- **Настройки заданий на уверенность** под комфорт в зале
- **Выбора стиля мотивации** и обратной связи
- **Планирования прогрессии** под цели и время

Проект готов на **100%** для end-to-end использования с продвинутой ИИ-персонализацией! 🎉