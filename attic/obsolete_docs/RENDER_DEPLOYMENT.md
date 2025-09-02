# Развертывание AI Fitness Coach на Render.com

## 1. Подготовка аккаунта Render.com

1. **Зарегистрируйтесь на [Render.com](https://render.com)**
2. **Подключите GitHub аккаунт** в настройках Render

## 2. Создание PostgreSQL базы данных

1. В Render Dashboard нажмите **"New" → "PostgreSQL"**
2. Настройки:
   - **Name**: `ai-fitness-coach-db`
   - **Database**: `ai_fitness_coach`
   - **User**: `ai_fitness_coach_user`
   - **Region**: Frankfurt (EU Central)
   - **Plan**: Free (для начала)
3. Нажмите **"Create Database"**
4. **Сохраните External Database URL** - понадобится для настройки приложения

## 3. Создание Redis для кеширования

1. В Render Dashboard нажмите **"New" → "Redis"**
2. Настройки:
   - **Name**: `ai-fitness-coach-redis`
   - **Region**: Frankfurt (EU Central)  
   - **Plan**: Free
3. Нажмите **"Create Redis"**
4. **Сохраните Redis URL** - понадобится для настройки

## 4. Создание Web Service

1. В Render Dashboard нажмите **"New" → "Web Service"**
2. **Connect Repository**: выберите `runowata/ai-fitness-coach`
3. Настройки:
   - **Name**: `ai-fitness-coach`
   - **Region**: Frankfurt (EU Central)
   - **Branch**: `main`
   - **Root Directory**: оставить пустым
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn config.wsgi:application`
   - **Plan**: Free (для начала)

## 5. Настройка переменных окружения

В разделе **Environment Variables** добавьте:

### Обязательные переменные:
```
DEBUG=False
SECRET_KEY=ваш-секретный-ключ-django
ALLOWED_HOSTS=ai-fitness-coach.onrender.com
DATABASE_URL=postgresql://[скопируйте из PostgreSQL сервиса]
REDIS_URL=redis://[скопируйте из Redis сервиса]
```

### OpenAI Integration:
```
OPENAI_API_KEY=ваш-openai-api-ключ
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.7
```

### Email (опционально):
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=ваш-email@gmail.com
EMAIL_HOST_PASSWORD=ваш-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=AI Fitness Coach <noreply@aifitnesscoach.com>
```

### AWS S3 (опционально, для медиа):
```
AWS_ACCESS_KEY_ID=ваш-aws-ключ
AWS_SECRET_ACCESS_KEY=ваш-aws-секрет
AWS_STORAGE_BUCKET_NAME=ваш-bucket
AWS_S3_REGION_NAME=eu-central-1
```

## 6. Генерация SECRET_KEY

Выполните в терминале:
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 7. Deploy и первоначальная настройка

1. Нажмите **"Create Web Service"**
2. Render автоматически начнет деплой
3. После успешного деплоя выполните миграции через Render Shell:

```bash
# В Render Dashboard → ваш сервис → Shell
python manage.py migrate
python manage.py loaddata fixtures/exercises.json
python manage.py loaddata fixtures/onboarding_questions.json
python manage.py loaddata fixtures/motivational_cards.json
python manage.py loaddata fixtures/stories.json
python manage.py loaddata fixtures/video_clips.json
python manage.py loaddata fixtures/achievements.json
python manage.py createsuperuser
```

## 8. Проверка развертывания

1. Откройте ваш URL: `https://ai-fitness-coach.onrender.com`
2. Проверьте:
   - ✅ Главная страница загружается
   - ✅ Регистрация работает
   - ✅ Онбординг проходится
   - ✅ Admin панель доступна

## 9. Мониторинг

- **Логи**: Render Dashboard → ваш сервис → Logs
- **Метрики**: Render Dashboard → ваш сервис → Metrics
- **Shell**: Для выполнения команд Django

## Готово! 🚀

Ваш AI Fitness Coach теперь доступен по адресу:
**https://ai-fitness-coach.onrender.com**

## Troubleshooting

### Если возникают ошибки:
1. Проверьте логи в Render Dashboard
2. Убедитесь что все environment variables настроены
3. Проверьте что DATABASE_URL и REDIS_URL корректные
4. При изменении кода делайте git push - Render автоматически обновится