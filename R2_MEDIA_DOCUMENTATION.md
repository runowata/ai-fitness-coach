# 📚 Документация: Медиатека AI Fitness Coach в Cloudflare R2

## 🎯 Общая информация

### Что загружаем
Полную медиатеку персонализированных фитнес-материалов для приложения **AI Fitness Coach** - Django-приложения для персональных тренировок для геев.

### Куда загружаем
**Cloudflare R2 Object Storage** - S3-совместимое облачное хранилище
- **Bucket:** `ai-fitness-media`
- **Account ID:** `92568f8b8a15c68a9ece5fe08c66485b`
- **Endpoint:** `https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com`
- **Public URL:** `https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev/`

### Технологии загрузки
- **Python 3.12** с библиотекой **boto3** (AWS SDK)
- **S3-совместимый API** для загрузки
- **10 параллельных потоков** для ускорения
- **SHA-256 хеширование** для предотвращения дубликатов
- **Автоматический перезапуск** при сбоях

---

## 📊 Структура медиатеки

### Общая статистика
- **Всего файлов:** 3,346
- **Общий размер:** 43.89 GB
- **Статус загрузки:** 99.97% (3345/3346 файлов)

### Детальная структура

#### 📹 Видео контент (1,333 файлов, ~43.3 GB)

| Категория | Количество | Путь в R2 | Описание |
|-----------|------------|-----------|----------|
| **Техника упражнений** | 147 | `videos/exercises/explain/` | Демонстрация правильной техники |
| **Напоминания** | 441 | `videos/reminders/` | Мотивационные напоминания |
| **Инструкции** | 423 | `videos/instructions/` | Пошаговые инструкции от тренеров |
| **Приветствия** | 15 | `videos/intros/` | Вступительные видео тренеров |
| **Еженедельная мотивация** | 5 | `videos/weekly/` | Недельные мотивационные ролики |
| **Завершение тренировки** | 10 | `videos/closing/` | Поздравления с завершением |
| **Ошибки в технике** | 134 | `videos/exercises/mistake/` | Демонстрация типичных ошибок |
| **Основная техника** | 158 | `videos/exercises/technique/` | Базовые упражнения |

#### 🖼️ Фото контент (2,000 файлов, ~0.56 GB)

| Категория | Количество | Путь в R2 | Описание |
|-----------|------------|-----------|----------|
| **Мотивационные цитаты** | 1,000 | `photos/quotes/` | Карточки с цитатами |
| **Тренировочные карточки** | 500 | `photos/workout/` | Визуальные подсказки |
| **Прогресс-карточки** | 500 | `photos/progress/` | Отслеживание достижений |

#### 👤 Дополнительный контент

| Категория | Количество | Путь в R2 | Описание |
|-----------|------------|-----------|----------|
| **Аватары тренеров** | 10 | `images/avatars/` | Фото виртуальных тренеров |
| **Служебные файлы** | 3 | корень | Скрипты и логи |

---

## 🔧 Интеграция с Render.com

### Переменные окружения для Render

```bash
# Основные ключи R2
R2_ACCESS_KEY_ID=3a9fd5a6b38ec994e057e33c1096874e
R2_SECRET_ACCESS_KEY=0817f9a3154b63b1968620a966e05e36f80fca0308ba91d9c8bf65e8622baa13
R2_ACCOUNT_ID=92568f8b8a15c68a9ece5fe08c66485b
R2_BUCKET=ai-fitness-media
R2_ENDPOINT=https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com

# Django Storage настройки
USE_R2_STORAGE=True
DEFAULT_FILE_STORAGE=storages.backends.s3boto3.S3Boto3Storage
AWS_S3_ENDPOINT_URL=${R2_ENDPOINT}
AWS_STORAGE_BUCKET_NAME=${R2_BUCKET}
AWS_S3_REGION_NAME=auto
AWS_S3_SIGNATURE_VERSION=s3v4
AWS_DEFAULT_ACL=private
AWS_QUERYSTRING_AUTH=True
AWS_QUERYSTRING_EXPIRE=3600
```

### Конфигурация Django (settings.py)

```python
# settings/production.py

import os

if os.environ.get('USE_R2_STORAGE') == 'True':
    # Cloudflare R2 Storage
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    AWS_ACCESS_KEY_ID = os.environ.get('R2_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('R2_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('R2_BUCKET')
    AWS_S3_ENDPOINT_URL = os.environ.get('R2_ENDPOINT')
    AWS_S3_REGION_NAME = 'auto'
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_DEFAULT_ACL = 'private'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_QUERYSTRING_AUTH = True
    AWS_QUERYSTRING_EXPIRE = 3600  # 1 час на signed URLs
    
    # Media files
    MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/'
```

### Использование в Django моделях

```python
# apps/workouts/models.py

class Exercise(models.Model):
    technique_video = models.FileField(
        upload_to='videos/exercises/technique/',
        blank=True
    )
    
    def get_video_url(self):
        """Генерирует signed URL для приватного доступа"""
        if self.technique_video:
            return self.technique_video.url  # django-storages автоматически создаст signed URL
        return None

# apps/content/models.py

class MotivationalCard(models.Model):
    image = models.ImageField(
        upload_to='photos/quotes/',
        blank=True
    )
    category = models.CharField(max_length=50)
    
    def get_cdn_url(self):
        """Получает публичный URL через CDN"""
        if self.image:
            # Для публичного доступа можно использовать pub-домен
            filename = self.image.name
            return f"https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev/{filename}"
        return None
```

---

## 🚀 Процесс развертывания

### 1. Установка зависимостей

```bash
# requirements.txt
django-storages==1.14.2
boto3==1.34.131
```

### 2. Миграция существующих файлов

```python
# management/commands/migrate_to_r2.py

from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from apps.workouts.models import Exercise
import boto3

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Пример миграции существующих файлов
        for exercise in Exercise.objects.all():
            if exercise.local_video_path:
                with open(exercise.local_video_path, 'rb') as f:
                    exercise.technique_video.save(
                        f"exercises/{exercise.slug}_technique.mp4",
                        f
                    )
```

### 3. Настройка CDN (опционально)

Для публичного доступа можно настроить Cloudflare CDN:
- Создать Custom Domain для R2 bucket
- Настроить правила кеширования
- Использовать для статичных ресурсов (фото)

---

## 💰 Экономика

### Стоимость хранения в R2
- **Хранение:** $0.015 за GB/месяц = **$0.66/месяц** за 44GB
- **Исходящий трафик:** **БЕСПЛАТНО** (главное преимущество R2)
- **Операции:** $0.36 за миллион запросов класса A

### Сравнение с Render Disk
| Параметр | Render Disk | Cloudflare R2 |
|----------|-------------|---------------|
| Хранение 44GB | ~$11/месяц | $0.66/месяц |
| Исходящий трафик | Платный | Бесплатный |
| Глобальная CDN | Нет | Да |
| Signed URLs | Нужно писать | Встроено |

---

## 📝 Скрипты управления

### Основные скрипты
- `upload_to_r2.py` - загрузка файлов в R2
- `check_upload_progress.py` - проверка прогресса
- `reliable_upload.sh` - надёжная загрузка с перезапуском
- `validate_media.py` - валидация медиатеки
- `fill_missing_media.py` - дозаполнение недостающих файлов

### Команды управления

```bash
# Проверить статус медиатеки
python check_upload_progress.py

# Валидация целостности
python validate_media.py

# Загрузить недостающие файлы
python upload_to_r2.py --auto

# Мониторинг в реальном времени
./monitor_upload.sh
```

---

## 🔒 Безопасность

### Приватный доступ
- Все файлы по умолчанию **приватные**
- Доступ через **Signed URLs** с временным токеном
- Срок жизни токена: 1 час (настраивается)

### Публичный доступ (для CDN)
- Домен: `https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev/`
- Использовать только для публичных ресурсов (карточки, аватары)
- Видео тренировок всегда через Signed URLs

---

## 📞 Контакты и поддержка

- **Cloudflare R2 Dashboard:** https://dash.cloudflare.com/
- **Render Dashboard:** https://dashboard.render.com/
- **Django Storages Docs:** https://django-storages.readthedocs.io/

---

*Документ обновлен: 8 августа 2025*
*Версия: 1.0*