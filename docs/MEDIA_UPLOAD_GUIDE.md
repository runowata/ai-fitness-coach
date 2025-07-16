# Руководство по загрузке медиа-контента

## Структура именования файлов

### Видео упражнений

#### Основные видео (техника и ошибки)
```
/videos/exercises/{exercise_slug}_technique_{model}.mp4
/videos/exercises/{exercise_slug}_mistake_{model}.mp4

Примеры:
- push-up_technique_mod1.mp4
- push-up_mistake_mod1.mp4
```

#### Инструктажи (по архетипам)
```
/videos/instructions/{exercise_slug}_instruction_{archetype}_{model}.mp4

Примеры:
- push-up_instruction_bro_mod1.mp4
- push-up_instruction_sergeant_mod2.mp4
- push-up_instruction_intellectual_mod3.mp4
```

#### Напоминания
```
/videos/reminders/{exercise_slug}_reminder_{archetype}_{number}.mp4

Примеры:
- push-up_reminder_bro_1.mp4
- push-up_reminder_bro_2.mp4
```

#### Мотивационные видео
```
/videos/motivation/weekly_{archetype}_week{number}.mp4
/videos/motivation/final_{archetype}.mp4

Примеры:
- weekly_bro_week1.mp4
- final_sergeant.mp4
```

### Изображения

#### Карточки мотивации
```
/images/cards/card_{category}_{number}.jpg

Примеры:
- card_goal_1.jpg
- card_experience_1.jpg
```

#### Аватары тренеров
```
/images/avatars/{archetype}_avatar_{number}.jpg

Примеры:
- bro_avatar_1.jpg
- sergeant_avatar_2.jpg
```

#### Обложки историй
```
/images/stories/{story_slug}_cover.jpg
/images/stories/{story_slug}_chapter_{number}.jpg

Примеры:
- confidence_journey_cover.jpg
- confidence_journey_chapter_1.jpg
```

## Процесс загрузки

### 1. Подготовка файлов
- Убедитесь, что все файлы соответствуют соглашению об именовании
- Видео должны быть в формате MP4 (H.264 + AAC)
- Изображения в формате JPG/PNG
- Оптимизируйте размер файлов (видео ≤ 4 Mbps)

### 2. Массовая загрузка через команду
```bash
# Проверка без загрузки
python manage.py import_media /path/to/media/folder --dry-run

# Загрузка с указанием категории
python manage.py import_media /path/to/videos --category exercise_technique

# Полная загрузка
python manage.py import_media /path/to/media/folder
```

### 3. Загрузка через админ-панель
1. Перейдите в раздел "Media Assets"
2. Нажмите "Add Media Asset"
3. Заполните форму:
   - Загрузите файл
   - Выберите категорию
   - Свяжите с упражнением (если применимо)
   - Укажите архетип тренера
   - Добавьте теги для поиска

### 4. Проверка CDN
После загрузки система автоматически:
- Загрузит файл в S3
- Создаст CDN-ссылку через CloudFront
- Обновит статус на "ready"

## Рекомендации

### Оптимизация видео
```bash
# Конвертация в оптимальный формат
ffmpeg -i input.mp4 -c:v h264 -crf 23 -c:a aac -b:a 128k -movflags +faststart output.mp4

# Изменение размера для мобильных
ffmpeg -i input.mp4 -vf scale=720:-1 -c:v h264 -crf 25 output_mobile.mp4
```

### Пакетная обработка изображений
```bash
# Оптимизация JPEG
jpegoptim --size=500k *.jpg

# Конвертация в WebP (для современных браузеров)
for f in *.jpg; do cwebp -q 80 "$f" -o "${f%.jpg}.webp"; done
```

## Контрольный список

- [ ] Все файлы названы согласно конвенции
- [ ] Видео в формате MP4 (H.264/AAC)
- [ ] Битрейт видео ≤ 4 Mbps
- [ ] Изображения оптимизированы (< 1MB)
- [ ] Создана резервная копия оригиналов
- [ ] Проверена работа на мобильных устройствах