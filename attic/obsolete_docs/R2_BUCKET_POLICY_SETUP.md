# Настройка публичного доступа R2 для мотивационных изображений

## Проблема
Мотивационные карточки возвращают `401 Unauthorized` потому что R2 bucket настроен как приватный.

## Решение

### Шаг 1: Применить bucket policy

1. **На сервере Render или локально** выполните:
```bash
cd "/Users/alexbel/Desktop/Проекты/AI Fitness Coach"
python apply_bucket_policy.py
```

2. **Если не хватает переменных окружения**, добавьте их:
```bash
export R2_ACCESS_KEY_ID='your-r2-access-key'  
export R2_SECRET_ACCESS_KEY='your-r2-secret-key'
```

### Шаг 2: Обновить URLs в базе данных

После применения bucket policy выполните:
```bash
python manage.py fix_motivational_card_urls --dry-run  # проверить что будет изменено
python manage.py fix_motivational_card_urls           # применить изменения
```

### Шаг 3: Проверить результат

Проверьте что изображение доступно:
```bash
curl -I https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev/photos/progress/card_progress_0066.jpg
```

Должен вернуться `HTTP/1.1 200 OK` (не 401 Unauthorized).

## Что делает bucket policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadMotivationalImages",
      "Effect": "Allow",
      "Principal": "*", 
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::ai-fitness-media/photos/progress/*"
    }
  ]
}
```

✅ **Безопасность:** Только папка `photos/progress/` становится публичной  
✅ **Приватность:** Остальные файлы остаются приватными  
✅ **Цель:** Мотивационные картинки отображаются в приложении  

## Файлы

- `apply_bucket_policy.py` - скрипт для применения политики
- `bucket_policy.json` - содержание политики  
- `fix_motivational_card_urls.py` - команда для исправления URLs