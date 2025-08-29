"""
Загрузка данных из реального Cloudflare R2 хранилища
"""
import boto3
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.workouts.models import R2Video, R2Image


class Command(BaseCommand):
    help = 'Load data from real Cloudflare R2 storage into simplified models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before loading',
        )
        parser.add_argument(
            '--videos-only',
            action='store_true',
            help='Load only videos',
        )
        parser.add_argument(
            '--images-only',
            action='store_true',
            help='Load only images',
        )

    def handle(self, *args, **options):
        self.stdout.write("🔄 ЗАГРУЗКА ДАННЫХ ИЗ РЕАЛЬНОГО R2...")
        
        # Настройки R2
        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        endpoint_url = os.environ.get('AWS_S3_ENDPOINT_URL')
        bucket_name = os.environ.get('AWS_STORAGE_BUCKET_NAME')
        
        if not all([aws_access_key_id, aws_secret_access_key, endpoint_url, bucket_name]):
            self.stdout.write(self.style.ERROR("❌ R2 credentials not found"))
            return
        
        # Очистка данных если запрошена
        if options.get('clear'):
            if not options.get('images_only'):
                R2Video.objects.all().delete()
                self.stdout.write("🗑️ Cleared all videos")
            if not options.get('videos_only'):
                R2Image.objects.all().delete()
                self.stdout.write("🗑️ Cleared all images")
        
        # Подключение к R2
        try:
            session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
            
            s3 = session.client(
                's3',
                endpoint_url=endpoint_url,
                region_name='auto'
            )
            
            self.stdout.write(f"✅ Connected to R2: {bucket_name}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ R2 connection failed: {e}"))
            return
        
        try:
            # Получаем все объекты
            all_objects = []
            paginator = s3.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=bucket_name):
                if 'Contents' in page:
                    all_objects.extend(page['Contents'])
            
            self.stdout.write(f"📊 Found {len(all_objects)} files in R2")
            
            # Загружаем видео
            if not options.get('images_only'):
                self._load_videos(all_objects)
            
            # Загружаем изображения
            if not options.get('videos_only'):
                self._load_images(all_objects)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error loading data: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())
    
    def _load_videos(self, all_objects):
        """Загружает видео из R2 в базу данных"""
        self.stdout.write("\n🎬 ЗАГРУЗКА ВИДЕО...")
        
        videos_to_create = []
        video_folders = {
            'videos/exercises/': 'exercises',
            'videos/motivation/': 'motivation', 
            'videos/final/': 'final',
            'videos/progress/': 'progress',
            'videos/weekly/': 'weekly',
        }
        
        for obj in all_objects:
            key = obj['Key']
            
            # Проверяем, что это видео в нужной папке
            for folder, category in video_folders.items():
                if key.startswith(folder) and key.endswith('.mp4'):
                    filename = key.split('/')[-1]
                    code = filename.replace('.mp4', '')
                    
                    # Генерируем название на основе кода
                    name = self._generate_video_name(code, category)
                    description = f"Видео {category}: {name}"
                    
                    videos_to_create.append(R2Video(
                        code=code,
                        name=name,
                        description=description,
                        category=category
                    ))
                    break
        
        # Массовая загрузка видео
        if videos_to_create:
            with transaction.atomic():
                R2Video.objects.bulk_create(videos_to_create, ignore_conflicts=True)
            
            self.stdout.write(f"✅ Loaded {len(videos_to_create)} videos")
            
            # Статистика по категориям
            for folder, category in video_folders.items():
                count = R2Video.objects.filter(category=category).count()
                self.stdout.write(f"  {category}: {count} videos")
        else:
            self.stdout.write("❌ No videos found")
    
    def _load_images(self, all_objects):
        """Загружает изображения из R2 в базу данных"""
        self.stdout.write("\n🖼️ ЗАГРУЗКА ИЗОБРАЖЕНИЙ...")
        
        images_to_create = []
        image_folders = {
            'images/avatars/': 'avatars',
            'photos/quotes/': 'quotes',
            'photos/progress/': 'progress', 
            'photos/workout/': 'workout',
        }
        
        for obj in all_objects:
            key = obj['Key']
            
            # Проверяем, что это изображение в нужной папке
            for folder, category in image_folders.items():
                if key.startswith(folder) and key.lower().endswith('.jpg'):
                    filename = key.split('/')[-1]
                    code = filename.replace('.jpg', '')
                    
                    # Генерируем название на основе кода
                    name = self._generate_image_name(code, category)
                    description = f"Изображение {category}: {name}"
                    
                    images_to_create.append(R2Image(
                        code=code,
                        name=name,
                        description=description,
                        category=category
                    ))
                    break
        
        # Массовая загрузка изображений
        if images_to_create:
            with transaction.atomic():
                R2Image.objects.bulk_create(images_to_create, ignore_conflicts=True)
            
            self.stdout.write(f"✅ Loaded {len(images_to_create)} images")
            
            # Статистика по категориям
            for folder, category in image_folders.items():
                count = R2Image.objects.filter(category=category).count()
                self.stdout.write(f"  {category}: {count} images")
        else:
            self.stdout.write("❌ No images found")
    
    def _generate_video_name(self, code, category):
        """Генерирует человеческое название для видео"""
        if category == 'exercises':
            if code.startswith('warmup_'):
                num = code.split('_')[1]
                return f"Разминка {num}"
            elif code.startswith('main_'):
                num = code.split('_')[1] 
                return f"Основное упражнение {num}"
            elif code.startswith('endurance_'):
                num = code.split('_')[1]
                return f"Выносливость {num}"
            elif code.startswith('relaxation_'):
                num = code.split('_')[1]
                return f"Расслабление {num}"
        
        elif category == 'motivation':
            if 'bro' in code:
                return f"Мотивация - Лучший друг"
            elif 'intellectual' in code:
                return f"Мотивация - Наставник"
            elif 'sergeant' in code:
                return f"Мотивация - Тренер"
        
        elif category == 'weekly':
            if 'week' in code:
                week_num = code.split('week')[-1].split('.')[0]
                return f"Еженедельное видео - неделя {week_num}"
        
        elif category == 'progress':
            return f"Видео прогресса"
        
        elif category == 'final':
            return f"Финальное видео"
        
        # Fallback
        return code.replace('_', ' ').title()
    
    def _generate_image_name(self, code, category):
        """Генерирует человеческое название для изображения"""
        if category == 'avatars':
            if 'best_mate' in code:
                return f"Аватар - Лучший друг"
            elif 'pro_coach' in code:
                return f"Аватар - Тренер" 
            elif 'wise_mentor' in code:
                return f"Аватар - Наставник"
        
        elif category == 'quotes':
            num = code.replace('card_quotes_', '').replace('card_quotes', '')
            return f"Мотивационная цитата {num}"
        
        elif category == 'progress':
            num = code.replace('card_progress_', '').replace('card_progress', '')
            return f"Карточка прогресса {num}"
            
        elif category == 'workout':
            num = code.replace('card_workout_', '').replace('card_workout', '')
            return f"Карточка тренировки {num}"
        
        # Fallback
        return code.replace('_', ' ').title()