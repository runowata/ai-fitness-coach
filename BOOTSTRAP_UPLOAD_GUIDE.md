# Bootstrap Data Upload Guide

## 📦 Архив готов к загрузке

- **Файл**: `workouts_bootstrap_v2.tar.gz` (135KB)
- **SHA256**: `89cc0035adb8291a753eb450dc73c222bd96883d184e342c84290d4e8114db38`
- **Содержимое**: `data/` директория с Excel файлами

## 🚀 Загрузка в R2

### Вариант 1: Автоматическая загрузка (рекомендуется)
```bash
python upload_bootstrap_archive.py
```

Скрипт запросит учётные данные R2 и загрузит архив в `bootstrap/workouts_bootstrap_v2.tar.gz`

### Вариант 2: Ручная загрузка через R2 Dashboard
1. Войдите в Cloudflare R2 Dashboard
2. Откройте ваш bucket
3. Создайте папку `bootstrap/`
4. Загрузите `workouts_bootstrap_v2.tar.gz` в `bootstrap/`
5. Установите публичный доступ (Public Read)

## 🌐 Переменные окружения для Render

После загрузки добавьте в Render → Environment:

```bash
BOOTSTRAP_DATA_URL=https://pub-xxxxx.r2.dev/bootstrap/workouts_bootstrap_v2.tar.gz
BOOTSTRAP_DATA_SHA256=89cc0035adb8291a753eb450dc73c222bd96883d184e342c84290d4e8114db38
BOOTSTRAP_DATA_VERSION=v2-2025-08-08
```

Замените `pub-xxxxx.r2.dev` на ваш реальный public domain R2.

## ✅ Проверка работы

После добавления переменных окружения:

1. Запустите **Manual Deploy** в Render
2. Команда `setup_v2_production` автоматически:
   - Скачает архив с проверкой SHA256
   - Распакует во временную директорию  
   - Импортирует данные
   - Сгенерирует тестовые планы

## 🔄 Обновление данных

Для обновления данных в будущем:
1. Пересоберите архив: `tar -czf workouts_bootstrap_v2.tar.gz data/`
2. Получите новый SHA256: `shasum -a 256 workouts_bootstrap_v2.tar.gz`
3. Загрузите новый архив
4. Обновите `BOOTSTRAP_DATA_SHA256` в Render
5. Запустите `python manage.py setup_v2_production --force-download`

## 📁 Структура архива

```
workouts_bootstrap_v2.tar.gz
└── data/
    ├── raw/
    │   ├── base_exercises.xlsx
    │   ├── base_exercises_original.xlsx
    │   ├── explainer_videos_111_nastavnik.xlsx
    │   ├── explainer_videos_222_professional.xlsx
    │   └── explainer_videos_333_rovesnik.xlsx
    └── clean/
        └── exercises.csv
```

## 🛠️ Команды для тестирования

Локальное тестирование автозагрузки:
```bash
# Переместить локальную папку для имитации production
mv data data_backup

# Установить переменную окружения
export BOOTSTRAP_DATA_URL="https://your-r2-domain.com/bootstrap/workouts_bootstrap_v2.tar.gz"
export BOOTSTRAP_DATA_SHA256="89cc0035adb8291a753eb450dc73c222bd96883d184e342c84290d4e8114db38"

# Запустить команду
python manage.py setup_v2_production

# Восстановить локальную папку
mv data_backup data
```