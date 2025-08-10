# Пошаговая инструкция: Настройка R2 для отображения изображений

## Проблема
Мотивационные карточки не отображаются из-за ошибки `401 Unauthorized` при доступе к изображениям R2.

## Решение
Применить bucket policy для публичного доступа к папке `photos/progress/`

---

## Способ 1: Через Render Shell (самый простой)

### Шаг 1: Открыть Render Shell
1. Зайти в [Render Dashboard](https://dashboard.render.com)
2. Найти сервис **ai-fitness-coach** (Web Service)
3. Перейти на вкладку **Shell**
4. Нажать **Launch Shell**

### Шаг 2: Выполнить команды в Shell
```bash
# 1. Перейти в директорию проекта
cd /opt/render/project/src

# 2. Запустить скрипт применения bucket policy
python apply_bucket_policy.py
```

**Ожидаемый результат:**
```
🔧 Применяем bucket policy к ai-fitness-media...
📋 Policy содержание:
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

✅ Bucket policy успешно применен!

🧪 Тестируем доступ...
curl -I https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev/photos/progress/card_progress_0066.jpg
✅ УСПЕХ! Изображения теперь доступны публично
```

### Шаг 3: Проверить результат
Открыть приложение и проверить что мотивационные карточки отображаются с изображениями.

---

## Способ 2: Через локальное окружение

### Шаг 1: Получить R2 credentials из Render
1. В Render Dashboard → Environment Variables
2. Найти и скопировать значения:
   - `R2_ACCESS_KEY_ID`
   - `R2_SECRET_ACCESS_KEY`

### Шаг 2: Установить credentials локально
```bash
export R2_ACCESS_KEY_ID='your-key-from-render'
export R2_SECRET_ACCESS_KEY='your-secret-from-render'
```

### Шаг 3: Установить зависимости
```bash
pip install boto3 requests
```

### Шаг 4: Запустить скрипт
```bash
cd "/Users/alexbel/Desktop/Проекты/AI Fitness Coach"
python apply_bucket_policy.py
```

---

## Способ 3: Через деплой (если другие способы не работают)

### Коммит изменений и деплой
```bash
git add apply_bucket_policy.py
git commit -m "Add R2 bucket policy setup script"
git push
```

### Выполнить через Deploy Hook
1. В Render Dashboard → Settings → Deploy Hooks
2. Создать Deploy Hook с командой:
   ```bash
   python apply_bucket_policy.py
   ```

---

## Что произойдет после применения

✅ **Изображения станут доступны публично по URL:**
- `https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev/photos/progress/card_progress_0066.jpg`

✅ **Мотивационные карточки отобразятся с изображениями**

✅ **Безопасность сохранена:**
- Только папка `/photos/progress/` стала публичной
- Остальные файлы остаются приватными

---

## Проверка результата

После применения проверить любой URL изображения:
```bash
curl -I https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev/photos/progress/card_progress_0066.jpg
```

**Должно вернуться:** `HTTP/1.1 200 OK` (не 401 Unauthorized)

---

## Файлы для справки

- `apply_bucket_policy.py` - скрипт применения политики  
- `bucket_policy.json` - содержание bucket policy
- `fix_motivational_card_urls.py` - команда исправления URLs (уже выполнена ✅)

## Если что-то пошло не так

1. **Проверить переменные окружения** в Render:
   - `R2_ACCESS_KEY_ID` 
   - `R2_SECRET_ACCESS_KEY`

2. **Проверить bucket name** в скрипте: должен быть `ai-fitness-media`

3. **Обратиться за помощью** если проблема не решается