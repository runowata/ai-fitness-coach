"""
Management command для синхронизации данных из R2 хранилища
Заменяет все Excel-based команды импорта
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.core.services.r2_scanner import R2StorageScanner
from apps.workouts.models import CSVExercise, R2Video, R2Image


class Command(BaseCommand):
    help = 'Синхронизирует CSVExercise и R2Video/R2Image записи из R2 хранилища'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет создано, но не создавать записи',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Пересоздать существующие записи',
        )
        parser.add_argument(
            '--exercises-only',
            action='store_true',
            help='Синхронизировать только CSVExercise',
        )
        parser.add_argument(
            '--videos-only',
            action='store_true',
            help='Синхронизировать только R2Video/R2Image',
        )
    
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.force = options['force']
        self.exercises_only = options['exercises_only'] 
        self.videos_only = options['videos_only']
        
        self.stdout.write("=" * 70)
        self.stdout.write("🔄 R2 STORAGE SYNC")
        self.stdout.write("=" * 70)
        
        if self.dry_run:
            self.stdout.write("⚠️  DRY RUN MODE - никакие записи не будут созданы")
        
        try:
            scanner = R2StorageScanner()
            
            # Сканируем R2 хранилище
            self.stdout.write("\n🔍 Сканируем R2 хранилище...")
            files = scanner.scan_r2_storage()
            
            if not files:
                self.stdout.write(self.style.WARNING("⚠️  Файлы в R2 не найдены"))
                return
            
            self.stdout.write(f"📁 Найдено {len(files)} медиа файлов")
            
            # Статистика по категориям
            categories = {}
            for file_info in files:
                category = file_info.category
                categories[category] = categories.get(category, 0) + 1
            
            self.stdout.write("📊 Статистика по категориям:")
            for category, count in categories.items():
                self.stdout.write(f"   {category}: {count} файлов")
            
            # Синхронизируем упражнения
            if not self.videos_only:
                self.sync_exercises(scanner, files)
            
            # Синхронизируем видео и изображения  
            if not self.exercises_only:
                self.sync_media(scanner, files)
            
            self.stdout.write(self.style.SUCCESS("\n✅ Синхронизация завершена успешно!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Ошибка синхронизации: {e}"))
            raise CommandError(f"Sync failed: {e}")
    
    def sync_exercises(self, scanner, files):
        """Синхронизирует CSVExercise записи"""
        self.stdout.write("\n📋 Синхронизация упражнений...")
        
        # Извлекаем упражнения из файлов
        exercises_data = scanner.extract_exercises_from_files(files)
        
        if not exercises_data:
            self.stdout.write("⚠️  Упражнения в R2 не найдены")
            return
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for exercise_id, data in exercises_data.items():
            try:
                if self.dry_run:
                    self.stdout.write(f"   [DRY RUN] Создал бы упражнение: {exercise_id} - {data['name_ru']}")
                    created_count += 1
                    continue
                
                # Проверяем существование
                exercise_exists = CSVExercise.objects.filter(id=exercise_id).exists()
                
                if exercise_exists and not self.force:
                    self.stdout.write(f"   ⏭️  Пропущено (уже существует): {exercise_id}")
                    skipped_count += 1
                    continue
                
                # Создаем или обновляем
                exercise, created = CSVExercise.objects.update_or_create(
                    id=exercise_id,
                    defaults={
                        'name_ru': data['name_ru'],
                        'description': data['description']
                    }
                )
                
                if created:
                    self.stdout.write(f"   ✅ Создано: {exercise_id} - {data['name_ru']}")
                    created_count += 1
                else:
                    self.stdout.write(f"   🔄 Обновлено: {exercise_id} - {data['name_ru']}")
                    updated_count += 1
                    
            except Exception as e:
                self.stdout.write(f"   ❌ Ошибка с {exercise_id}: {e}")
        
        # Итоговая статистика
        self.stdout.write(f"\n📊 Результаты синхронизации упражнений:")
        self.stdout.write(f"   ✅ Создано: {created_count}")
        self.stdout.write(f"   🔄 Обновлено: {updated_count}")  
        self.stdout.write(f"   ⏭️  Пропущено: {skipped_count}")
    
    def sync_media(self, scanner, files):
        """Синхронизирует R2Video и R2Image записи"""
        self.stdout.write("\n🎥 Синхронизация медиа файлов...")
        
        # Разделяем видео и изображения
        video_files = [f for f in files if f.key.startswith('videos/')]
        # Ищем изображения в images/ и photos/
        image_files = [f for f in files if f.key.startswith('images/') or f.key.startswith('photos/')]
        
        self.stdout.write(f"   Видео файлов: {len(video_files)}")
        self.stdout.write(f"   Изображений: {len(image_files)}")
        
        # Синхронизируем видео
        if video_files:
            self.sync_r2_videos(scanner, video_files)
        
        # Синхронизируем изображения  
        if image_files:
            self.sync_r2_images(scanner, image_files)
    
    def sync_r2_videos(self, scanner, video_files):
        """Синхронизирует R2Video записи"""
        self.stdout.write("\n🎬 Синхронизация R2Video...")
        
        videos_data = scanner.create_r2_video_data(video_files)
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for video_data in videos_data:
            try:
                code = video_data['code']
                
                if self.dry_run:
                    self.stdout.write(f"   [DRY RUN] Создал бы видео: {code}")
                    created_count += 1
                    continue
                
                # Проверяем существование
                video_exists = R2Video.objects.filter(code=code).exists()
                
                if video_exists and not self.force:
                    skipped_count += 1
                    continue
                
                # Создаем или обновляем
                video, created = R2Video.objects.update_or_create(
                    code=code,
                    defaults=video_data
                )
                
                if created:
                    created_count += 1
                    if created_count % 50 == 0:  # Прогресс каждые 50 записей
                        self.stdout.write(f"   📈 Обработано {created_count} видео...")
                else:
                    updated_count += 1
                    
            except Exception as e:
                self.stdout.write(f"   ❌ Ошибка с {code}: {e}")
        
        self.stdout.write(f"\n📊 Результаты синхронизации R2Video:")
        self.stdout.write(f"   ✅ Создано: {created_count}")
        self.stdout.write(f"   🔄 Обновлено: {updated_count}")
        self.stdout.write(f"   ⏭️  Пропущено: {skipped_count}")
    
    def sync_r2_images(self, scanner, image_files):
        """Синхронизирует R2Image записи"""
        self.stdout.write("\n🖼️  Синхронизация R2Image...")
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for file_info in image_files:
            try:
                # Код = имя файла без расширения
                code = file_info.filename.rsplit('.', 1)[0]
                
                if self.dry_run:
                    self.stdout.write(f"   [DRY RUN] Создал бы изображение: {code}")
                    created_count += 1
                    continue
                
                # Проверяем существование  
                image_exists = R2Image.objects.filter(code=code).exists()
                
                if image_exists and not self.force:
                    skipped_count += 1
                    continue
                
                # Генерируем название
                name = code.replace('_', ' ').title()
                
                # Создаем или обновляем
                image, created = R2Image.objects.update_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'description': f'Изображение {name} (автоматически созданное из R2)',
                        'category': self._map_image_category(file_info.category),
                        'archetype': scanner._map_archetype_to_model(file_info.archetype) if file_info.archetype else ''
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                    
            except Exception as e:
                self.stdout.write(f"   ❌ Ошибка с {file_info.filename}: {e}")
        
        self.stdout.write(f"\n📊 Результаты синхронизации R2Image:")
        self.stdout.write(f"   ✅ Создано: {created_count}")
        self.stdout.write(f"   🔄 Обновлено: {updated_count}")
        self.stdout.write(f"   ⏭️  Пропущено: {skipped_count}")
    
    def _map_image_category(self, r2_category: str) -> str:
        """Маппит категории изображений из R2 в модель R2Image"""
        mapping = {
            'avatars': 'avatars',
            'quotes': 'quotes', 
            'progress': 'progress',
            'workout': 'workout'
        }
        return mapping.get(r2_category, 'avatars')