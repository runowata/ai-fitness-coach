# AI Fitness Coach

Веб-приложение, предоставляющее персонализированные программы тренировок для мужчин-геев. Приложение сочетает в себе фитнес, задачи по развитию уверенности и наградной эротический контент.

## Ключевые функции

* **Интерактивный онбординг** с мгновенной мотивирующей обратной связью
* **Выбор AI-тренера** из трех архетипов (Наставник, Профессионал, Ровесник)
* **AI-генерация плана** с еженедельной адаптацией на основе прогресса
* **Ежедневные тренировки** с возможностью замены упражнений
* **Система XP и достижений** с разблокировкой эксклюзивного контента
* **Еженедельные уроки** персонализированные по архетипу тренера
* **Микро-обратная связь** после каждой тренировки
* **Задания на развитие уверенности**

## Технический стек

* **Backend:** Python 3.12+ / Django 5.x
* **Database:** PostgreSQL
* **Storage:** Amazon S3 + CloudFront CDN
* **AI:** OpenAI GPT-4 / Google Gemini
* **Deployment:** Render.com
* **Monitoring:** Grafana / Prometheus

## Установка и запуск

### Требования
* Python 3.12+
* PostgreSQL 15+
* Redis (для кеширования)
* AWS аккаунт для S3

### Локальная разработка

```bash
# Клонирование репозитория
git clone https://github.com/your-org/ai-fitness-coach.git
cd ai-fitness-coach

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env файл

# Миграции базы данных
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser

# Импорт медиа-контента
python manage.py import_media --dry-run  # Тестовый запуск
python manage.py import_media  # Реальный импорт

# Запуск сервера разработки
python manage.py runserver
```

## Структура проекта

```
ai_fitness_coach/
├── apps/
│   ├── users/          # Аутентификация и профили
│   ├── workouts/       # Тренировки и упражнения
│   ├── onboarding/     # Опросник и генерация плана
│   ├── content/        # Медиа-контент и рассказы
│   ├── achievements/   # Достижения и XP-система
│   └── ai_integration/ # Интеграция с AI
├── config/             # Настройки Django
├── static/             # Статические файлы
├── media/              # Локальные медиа (dev only)
├── templates/          # HTML шаблоны
├── locale/             # Переводы
└── tests/              # Тесты
```

## Безопасность

* Хранение паролей: Argon2
* 2FA: TOTP (опционально)
* Rate limiting: 10 req/min для критичных эндпоинтов
* Age verification: 18+ подтверждение при регистрации
* GDPR compliance: согласие на обработку данных

## Нефункциональные требования

* Время ответа API: < 300ms (95-й перцентиль)
* SLA медиа-хостинга: 99.9%
* Покрытие unit-тестами: ≥ 80%
* Поддержка браузеров: последние 2 версии Chrome, Safari, Firefox, Edge

## Медиа-контент

### Видео спецификации
* Кодеки: H.264 + AAC
* Битрейт: ≤ 4 Mbps
* Разрешение: 1080p (основной), 720p (мобильный)

### Структура хранения
```
/videos/{exercise_slug}/{type}/{archetype}.mp4
/images/cards/{card_id}.jpg
/images/avatars/{archetype}_{number}.jpg
```

## Backend v0.9 API

### Weekly Lesson Endpoints

```http
GET /api/weekly/current/
```
Возвращает текущий непрочитанный урок недели и помечает его как прочитанный.

**Response:**
```json
{
  "id": 123,
  "week": 3,
  "archetype": "111",
  "lesson_title": "Строим привычку",
  "lesson_script": "Третья неделя — закрепление основ...",
  "created_at": "2025-08-06T10:00:00Z",
  "is_read": true
}
```

```http
GET /api/weekly/unread/
```
Проверяет наличие непрочитанных уроков (для индикатора в UI).

**Response:**
```json
{
  "unread": true
}
```

```http
GET /api/weekly/{week}/
```
Получает урок по номеру недели для архетипа текущего пользователя.

**Response:**
```json
{
  "week": 3,
  "archetype": "111",
  "title": "Строим привычку",
  "script": "Третья неделя — закрепление основ...",
  "locale": "ru",
  "duration_sec": 180
}
```

### Other API Endpoints

```http
PATCH /api/archetype/
```
Обновляет архетип пользователя.

```http
GET /api/exercise/{exercise_id}/video/
```
Получает видео-инструкцию для упражнения.

```http
GET /healthz/
```
Системный мониторинг (база данных, Redis, AI интеграция).

### Authentication
Все API endpoints требуют аутентификации. Используется Django сессионная аутентификация.

## Команда и роли

* **Admin** - полный доступ к системе
* **ContentManager** - управление медиа и текстами
* **Moderator** - модерация пользовательского контента
* **User** - обычный пользователь

## Метрики и отчетность

Основные метрики отслеживаются через Grafana:
* DAU/MAU
* Средняя длина streak
* % завершивших курс
* Конверсия по этапам онбординга
* Время выполнения тренировок

## Лицензирование

Все медиа-материалы являются собственностью компании. Возможность удаления контента по запросу DMCA.