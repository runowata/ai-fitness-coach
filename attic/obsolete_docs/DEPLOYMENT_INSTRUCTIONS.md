# AI Fitness Coach - Deployment Instructions

## Обзор изменений

Реализован архитектурный рефакторинг для замены быстрых фиксов на масштабируемые решения:

### 1. VideoStorage Abstraction Layer
- **VideoProvider**: Поддержка R2, Stream, External URL
- **Storage Adapters**: R2Adapter, StreamAdapter, ExternalAdapter  
- **Protocol-based**: Легко добавлять новые провайдеры

### 2. Pydantic Schema Validation
- **Strict AI Response Validation**: Валидация структуры, типов, ограничений
- **WorkoutPlan Schema**: Проверка недель, дней, упражнений
- **Error Handling**: Понятные сообщения об ошибках

### 3. Exercise Validation Refactoring  
- **Provider Agnostic**: Работает с любым storage provider
- **Performance**: Оптимизированные запросы с кешированием
- **Reliability**: Graceful error handling

### 4. Comprehensive Testing
- **Unit Tests**: Моки для всех компонентов
- **Integration Tests**: End-to-end user flow
- **Performance Tests**: Большие плейлисты, edge cases

---

## Pre-deployment Checklist

### 1. Code Review
```bash
# Проверка всех новых файлов
git status
git diff --name-only origin/main

# Ключевые файлы для review:
# - apps/workouts/models.py (новые поля)  
# - apps/workouts/video_storage.py (новый слой абстракции)
# - apps/ai_integration/schemas.py (Pydantic валидация)
# - apps/workouts/migrations/0016_*.py (миграция)
```

### 2. Environment Variables
```bash
# Убедитесь что настроены:
echo $OPENAI_API_KEY
echo $R2_ENDPOINT  
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY

# Опционально для Stream (будущее):
echo $CF_STREAM_HLS_TEMPLATE
```

### 3. Dependencies Check
```bash
# Проверка что Pydantic установлен
pip show pydantic
# Должна быть версия >= 2.0.0

# Если не установлен:
pip install pydantic>=2.0.0
```

---

## Deployment Steps

### Шаг 1: Run Tests Locally
```bash
# Запустить все тесты перед деплоем
pytest tests/ -v

# Запустить только новые тесты
pytest tests/test_video_storage.py -v
pytest tests/test_ai_schemas.py -v  
pytest tests/test_exercise_validation.py -v
pytest tests/test_video_playlist_builder.py -v
pytest tests/test_e2e_user_flow.py -v

# Тестирование с coverage
pytest --cov=apps --cov-report=html
```

### Шаг 2: Database Migration
```bash
# КРИТИЧЕСКИ ВАЖНО: Выполнить миграцию до deployment
python manage.py migrate --plan
python manage.py migrate

# Проверить что миграция прошла успешно
python manage.py showmigrations workouts
```

### Шаг 3: Validation Test  
```bash
# Тестирование валидации AI ответов
python manage.py shell
>>> from apps.ai_integration.schemas import validate_ai_plan_response
>>> test_json = '{"plan_name": "Test", "duration_weeks": 4, "goal": "Test goal", "weeks": []}'
>>> validate_ai_plan_response(test_json)  # Должно выдать ошибку
```

### Шаг 4: Storage Adapter Test
```bash
# Тестирование video storage
python manage.py shell
>>> from apps.workouts.video_storage import get_storage, R2Adapter
>>> from apps.workouts.models import VideoClip
>>> # Создать тестовый clip с provider='r2' 
>>> adapter = R2Adapter()
>>> print("R2 adapter working")
```

### Шаг 5: Deploy & Smoke Test
```bash
# После деплоя на Render:
# 1. Проверить health check
curl https://your-app.onrender.com/healthz/

# 2. Проверить что миграции применены
# В Render console:
python manage.py showmigrations workouts

# 3. Тест полного user flow
# - Создать тестового юзера
# - Пройти onboarding
# - Нажать "Начать Тренировку" 
# - Проверить что нет 500 ошибок
```

---

## Rollback Plan

В случае проблем после деплоя:

### Быстрый Rollback  
```bash
# 1. Откатить к предыдущему коммиту
git revert HEAD --no-edit
git push

# 2. Render автоматически подхватит изменения
```

### Database Rollback (если нужен)
```bash
# ТОЛЬКО в крайнем случае - может потерять данные!
python manage.py migrate workouts 0015_merge_state_only_and_0012
```

### Emergency Hotfix
Если нужно быстро отключить новую валидацию:
```python
# В apps/ai_integration/services.py временно:
# Закомментировать строки 271-281 (новая валидация)
# Раскомментировать строки 284-289 (старый метод)
```

---

## Post-deployment Verification

### 1. Functionality Tests
```bash
# Создать тест-пользователя через admin
# Пройти полный onboarding flow
# Проверить генерацию плана
# Проверить отображение видео в тренировках
```

### 2. Performance Monitoring
```bash
# Проверить время ответа AI
# Мониторить количество ошибок валидации
# Проверить время загрузки плейлистов
```

### 3. Error Monitoring  
```bash
# Проверить логи на наличие:
# - Pydantic ValidationError
# - AI client timeouts
# - Video storage errors
```

---

## Advanced Configuration

### Cloudflare Stream Setup (Будущее)
```python
# В settings.py добавить:
CF_STREAM_HLS_TEMPLATE = "https://videodelivery.net/{playback_id}/manifest/video.m3u8"

# В admin создать VideoClip с:
# provider = "stream"
# stream_uid = "your-stream-id"
```

### Custom Storage Providers
```python
# Создать новый adapter в video_storage.py:
class CustomAdapter:
    def exists(self, clip): pass
    def playback_url(self, clip): pass

# Добавить в get_storage():
elif clip.provider == "custom":
    return CustomAdapter()
```

### Performance Tuning
```python  
# В settings.py:
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL'),
        'KEY_PREFIX': 'fitness_coach',
        'TIMEOUT': 300,  # 5 минут для exercise validation
    }
}
```

---

## Troubleshooting

### Common Issues & Solutions

**1. ValidationError: AI response validation failed**
```bash
# Проверить что AI возвращает корректный JSON
# Посмотреть логи для детальной ошибки
# Временно отключить валидацию если критично
```

**2. VideoStorage adapter not found**  
```bash
# Проверить что поле provider установлено в r2
# Запустить data migration повторно
python manage.py migrate workouts 0016 --fake
python manage.py migrate workouts 0016
```

**3. Exercise validation returning empty set**
```bash  
# Очистить кеш валидации
python manage.py shell
>>> from apps.core.services.exercise_validation import ExerciseValidationService
>>> ExerciseValidationService.invalidate_cache()
```

**4. Video playlists empty**
```bash
# Проверить что VideoClip записи имеют provider='r2'
# Проверить что r2_file поля заполнены
# Проверить storage adapter
```

### Debug Commands
```bash
# Проверить провайдеры видео
python manage.py shell
>>> from apps.workouts.models import VideoClip
>>> VideoClip.objects.values('provider').distinct()

# Проверить валидацию упражнений  
>>> from apps.core.services.exercise_validation import ExerciseValidationService
>>> slugs = ExerciseValidationService.get_allowed_exercise_slugs()
>>> print(f"Valid exercises: {len(slugs)}")

# Тест генерации плейлиста
>>> from apps.workouts.services import VideoPlaylistBuilder
>>> builder = VideoPlaylistBuilder(archetype="professional")
# Создать mock workout и проверить playlist
```

---

## Success Metrics

После успешного деплоя должны наблюдаться:

- ✅ **Уменьшение 500 ошибок** при нажатии "Начать Тренировку"  
- ✅ **Стабильная генерация AI планов** с правильным количеством недель
- ✅ **Работающие видео плейлисты** для всех архетипов
- ✅ **Быстрая валидация упражнений** через провайдер-агностический слой
- ✅ **Готовность к добавлению Cloudflare Stream** без изменения кода

**Архитектурные преимущества:**
- Код готов к масштабированию
- Легко добавлять новые video providers
- Строгая типизация AI ответов
- Comprehensive test coverage
- Отсутствие технического долга