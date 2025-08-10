# 📋 Инструкция: Создание GitHub Release для Bootstrap архива

## 🚀 Быстрая инструкция

### 1. Создать Release на GitHub

1. Перейдите в репозиторий: https://github.com/runowata/ai-fitness-coach
2. Нажмите **"Releases"** → **"Create a new release"**
3. Заполните:
   - **Tag version**: `bootstrap-v2.0.0`
   - **Release title**: `Bootstrap Data v2.0.0`
   - **Description**: Вставьте описание ниже
   - **Attach binaries**: Загрузите файл `workouts_bootstrap_v2.tar.gz`

### 2. Описание для Release

```markdown
# 📦 Workout Bootstrap Data v2.0.0

**Archive**: `workouts_bootstrap_v2.tar.gz` (135KB)  
**SHA256**: `89cc0035adb8291a753eb450dc73c222bd96883d184e342c84290d4e8114db38`  
**Date**: 2025-08-08

## 📋 Contents
- Exercise database (147 exercises)
- Video metadata for R2 organization  
- Archetype-specific content mapping (peer/professional/mentor)

## 🔧 Usage in Production

Set these environment variables in Render:

```bash
BOOTSTRAP_DATA_URL=https://github.com/runowata/ai-fitness-coach/releases/download/bootstrap-v2.0.0/workouts_bootstrap_v2.tar.gz
BOOTSTRAP_DATA_SHA256=89cc0035adb8291a753eb450dc73c222bd96883d184e342c84290d4e8114db38
BOOTSTRAP_DATA_VERSION=v2-2025-08-08
```

Then run **Manual Deploy** - the system will auto-download and import data.

## 🗂️ Archive Structure
```
workouts_bootstrap_v2.tar.gz
└── data/
    ├── raw/
    │   ├── base_exercises.xlsx
    │   ├── explainer_videos_111_nastavnik.xlsx
    │   ├── explainer_videos_222_professional.xlsx
    │   └── explainer_videos_333_rovesnik.xlsx
    └── clean/
        └── exercises.csv
```
```

### 3. Environment Variables для Render

После создания Release добавьте в Render → Environment:

```bash
BOOTSTRAP_DATA_URL=https://github.com/runowata/ai-fitness-coach/releases/download/bootstrap-v2.0.0/workouts_bootstrap_v2.tar.gz
BOOTSTRAP_DATA_SHA256=89cc0035adb8291a753eb450dc73c222bd96883d184e342c84290d4e8114db38  
BOOTSTRAP_DATA_VERSION=v2-2025-08-08
```

### 4. Запуск деплоя

1. Добавьте переменные в Render
2. Нажмите **Manual Deploy**
3. В логах увидите: 
   ```
   🌐 Downloading bootstrap data from cloud...
   📦 Version: v2-2025-08-08
   🔐 SHA256 verified
   ✅ Import completed
   ```

## ✅ Результат

После успешного деплоя:
- БД заполнена упражнениями 
- Видеоклипы настроены для R2
- Система готова к работе
- Никаких ручных загрузок данных не требуется

---

## 📁 Локальный архив готов

- **Файл**: `workouts_bootstrap_v2.tar.gz` (135,186 байт)
- **Путь**: `/Users/alexbel/Desktop/Проекты/AI Fitness Coach/workouts_bootstrap_v2.tar.gz`
- **SHA256**: `89cc0035adb8291a753eb450dc73c222bd96883d184e342c84290d4e8114db38`