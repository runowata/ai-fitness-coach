"""
Management command to explore real R2 storage structure
Исследует реальную структуру Cloudflare R2 хранилища
"""
import boto3
import os
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Explore complete R2 storage structure and catalog all files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed file listings for each folder',
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 ИССЛЕДОВАНИЕ РЕАЛЬНОЙ СТРУКТУРЫ R2...")
        
        # Получаем настройки R2 из окружения или Django settings
        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        endpoint_url = os.environ.get('AWS_S3_ENDPOINT_URL')
        bucket_name = os.environ.get('AWS_STORAGE_BUCKET_NAME')
        
        if not all([aws_access_key_id, aws_secret_access_key, endpoint_url, bucket_name]):
            self.stdout.write(self.style.ERROR("❌ R2 credentials not found in environment"))
            self.stdout.write("Set these environment variables:")
            self.stdout.write("- AWS_ACCESS_KEY_ID")
            self.stdout.write("- AWS_SECRET_ACCESS_KEY") 
            self.stdout.write("- AWS_S3_ENDPOINT_URL")
            self.stdout.write("- AWS_STORAGE_BUCKET_NAME")
            return
        
        # Инициализируем клиент R2
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
            
            self.stdout.write(f"✅ Подключение к R2: {bucket_name}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка подключения к R2: {e}"))
            return
        
        try:
            # Получаем ВСЕ объекты в bucket
            all_objects = []
            paginator = s3.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=bucket_name):
                if 'Contents' in page:
                    all_objects.extend(page['Contents'])
            
            self.stdout.write(f"📊 Найдено {len(all_objects)} файлов в R2")
            
            # Анализируем структуру папок
            folder_structure = defaultdict(list)
            file_types = defaultdict(int)
            
            for obj in all_objects:
                key = obj['Key']
                size = obj['Size']
                
                # Определяем папку
                if '/' in key:
                    folder = '/'.join(key.split('/')[:-1])
                    filename = key.split('/')[-1]
                else:
                    folder = 'root'
                    filename = key
                
                folder_structure[folder].append({
                    'name': filename,
                    'size': size,
                    'full_path': key
                })
                
                # Подсчитываем типы файлов
                if '.' in filename:
                    ext = filename.split('.')[-1].lower()
                    file_types[ext] += 1
            
            # Выводим структуру
            self.stdout.write("\n" + "="*70)
            self.stdout.write("📁 СТРУКТУРА ПАПОК R2:")
            self.stdout.write("="*70)
            
            for folder, files in sorted(folder_structure.items()):
                # Группируем файлы по типам в этой папке
                folder_types = defaultdict(list)
                total_size = 0
                
                for file_info in files:
                    filename = file_info['name']
                    size = file_info['size']
                    total_size += size
                    
                    if '.' in filename:
                        ext = filename.split('.')[-1].lower()
                        folder_types[ext].append(filename)
                    else:
                        folder_types['no_ext'].append(filename)
                
                # Размер папки в MB
                size_mb = total_size / (1024 * 1024)
                
                self.stdout.write(f"\n📂 {folder} ({len(files)} файлов, {size_mb:.1f} MB)")
                
                for ext, file_list in sorted(folder_types.items()):
                    self.stdout.write(f"  .{ext}: {len(file_list)} файлов")
                    
                    if options.get('detailed') and len(file_list) <= 20:
                        for filename in sorted(file_list):
                            self.stdout.write(f"    - {filename}")
                    elif options.get('detailed') and len(file_list) > 20:
                        self.stdout.write(f"    - {file_list[0]} ... {file_list[-1]} (показаны первый и последний)")
            
            # Общая статистика по типам файлов
            self.stdout.write("\n" + "="*70)
            self.stdout.write("📈 СТАТИСТИКА ПО ТИПАМ ФАЙЛОВ:")
            self.stdout.write("="*70)
            
            for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
                self.stdout.write(f"  .{ext}: {count} файлов")
            
            # Анализ видео по категориям
            self.stdout.write("\n" + "="*70)
            self.stdout.write("🎬 АНАЛИЗ ВИДЕО ПО КАТЕГОРИЯМ:")
            self.stdout.write("="*70)
            
            video_analysis = defaultdict(int)
            for folder, files in folder_structure.items():
                if 'videos' in folder.lower():
                    mp4_files = [f for f in files if f['name'].endswith('.mp4')]
                    if mp4_files:
                        category = folder.split('/')[-1] if '/' in folder else folder
                        video_analysis[f"{folder} ({category})"] = len(mp4_files)
            
            for category, count in sorted(video_analysis.items()):
                self.stdout.write(f"  {category}: {count} видео")
            
            # Анализ изображений для карточек
            self.stdout.write("\n" + "="*70)
            self.stdout.write("🖼️ АНАЛИЗ ИЗОБРАЖЕНИЙ:")
            self.stdout.write("="*70)
            
            image_folders = {}
            image_exts = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            
            for folder, files in folder_structure.items():
                image_files = [f for f in files if any(f['name'].lower().endswith(f'.{ext}') for ext in image_exts)]
                if image_files:
                    image_folders[folder] = len(image_files)
                    if 'card' in folder.lower() or 'motivation' in folder.lower():
                        self.stdout.write(f"  📋 {folder}: {len(image_files)} изображений")
                        if options.get('detailed'):
                            for img in image_files[:10]:  # Показываем первые 10
                                self.stdout.write(f"    - {img['name']} ({img['size']} bytes)")
            
            # Итоговые рекомендации
            self.stdout.write("\n" + "="*70)
            self.stdout.write("💡 РЕКОМЕНДАЦИИ ДЛЯ БАЗЫ ДАННЫХ:")
            self.stdout.write("="*70)
            
            total_videos = sum(video_analysis.values())
            total_images = sum(image_folders.values())
            
            self.stdout.write(f"1. Создать таблицы для {total_videos} видео")
            self.stdout.write(f"2. Создать таблицы для {total_images} изображений") 
            self.stdout.write("3. Структура видео должна отражать папки R2")
            self.stdout.write("4. Добавить поддержку мотивационных карточек")
            self.stdout.write("5. Настроить правильные размеры изображений")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка исследования R2: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())