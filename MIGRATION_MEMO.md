# ПАМЯТКА ДЛЯ ПЕРЕСОЗДАНИЯ МИГРАЦИЙ

## Текущее состояние моделей (что должно быть в итоге):

### apps/workouts/models.py:
1. **R2Video** - основная модель для видео из R2:
   - code (PK, CharField)
   - name (CharField) 
   - description (TextField, blank=True)
   - category (CharField, choices: exercises, motivation, final, progress, weekly)
   - archetype (CharField, choices: mentor, professional, peer, blank=True)
   - display_title (CharField, blank=True) - для landing page
   - display_description (TextField, blank=True) - для landing page
   - is_featured (BooleanField, default=False) - для landing page
   - sort_order (PositiveIntegerField, default=0) - для landing page

2. **R2Image** - основная модель для изображений из R2:
   - code (PK, CharField)
   - name (CharField)
   - description (TextField, blank=True)  
   - category (CharField, choices: avatars, quotes, progress, workout)
   - archetype (CharField, choices: mentor, professional, peer, blank=True)
   - alt_text (CharField, blank=True) - для landing page
   - is_hero_image (BooleanField, default=False) - для landing page
   - is_featured (BooleanField, default=False) - для landing page
   - sort_order (PositiveIntegerField, default=0) - для landing page

3. **DailyPlaylistItem**:
   - day (ForeignKey to DailyWorkout)
   - order (PositiveIntegerField)
   - role (CharField, choices)
   - **video** (ForeignKey to R2Video) - НЕ media!
   - duration_seconds (PositiveIntegerField, null=True)
   - overlay (JSONField, default=dict)

4. Другие модели: WorkoutPlan, DailyWorkout, CSVExercise, etc. - без изменений

### apps/content/models.py:
1. **LandingContent** - ТОЛЬКО эта модель остается
   - version, hero_title, hero_subtitle, etc.

2. **УДАЛЕНЫ:**
   - ~~MediaAsset~~ - заменен на R2Video/R2Image
   - ~~TrainerPersona~~ - заменен на архетипы в R2Video/R2Image

## Структура миграций которая должна получиться:

### apps/workouts/migrations/:
- 0001_initial.py - все базовые модели 
- 0002_create_r2_models.py - R2Video, R2Image
- 0003_add_landing_fields_to_r2_models.py - поля для landing page

### apps/content/migrations/:
- 0001_initial.py - LandingContent (без MediaAsset, TrainerPersona)

## Важные зависимости:
- DailyPlaylistItem.video -> workouts.R2Video (НЕ content.MediaAsset!)
- UnifiedMediaService работает с R2Video/R2Image
- Архетипы хранятся в самих медиафайлах, не в отдельной модели

## Данные для загрузки после миграций:
1. python manage.py load_r2_data (616 видео, 2009 изображений)
2. Архетипы для аватаров уже настроены в коде загрузки