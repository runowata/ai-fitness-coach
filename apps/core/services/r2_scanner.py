"""
R2 Storage Scanner Service
Автоматически анализирует R2 хранилище и создает CSVExercise + R2Video записи
"""
import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from django.conf import settings
import boto3
from botocore.client import Config

logger = logging.getLogger(__name__)


@dataclass
class R2FileInfo:
    """Информация о файле в R2"""
    key: str  # полный путь: videos/exercises/main_001_technique_mentor.mp4
    size: int
    last_modified: str
    filename: str  # main_001_technique_mentor.mp4
    category: str  # exercises, motivation, etc.
    exercise_id: Optional[str] = None  # main_001
    video_type: Optional[str] = None  # technique, instruction, mistake
    archetype: Optional[str] = None  # mentor, professional, peer


class R2StorageScanner:
    """
    Сканер R2 хранилища для автоматического создания данных
    
    Принцип работы:
    1. Сканирует все файлы в R2
    2. Парсит naming convention
    3. Автоматически создает CSVExercise + R2Video
    """
    
    # Архетипы в файлах
    ARCHETYPE_MAPPING = {
        'mentor': 'mentor',
        'nastavnik': 'mentor', 
        'm01': 'mentor',
        'professional': 'professional',
        'pro': 'professional',
        'p01': 'professional', 
        'peer': 'peer',
        'rovesnik': 'peer',
        'r01': 'peer'
    }
    
    # Типы видео
    VIDEO_TYPES = {
        'instruction': 'instruction',
        'technique': 'technique', 
        'mistake': 'mistake',
        'reminder': 'reminder',
        'motivation': 'motivation'
    }
    
    # Категории упражнений по префиксам
    EXERCISE_CATEGORIES = {
        'warmup_': 'warmup',
        'main_': 'main', 
        'endurance_': 'endurance',
        'relaxation_': 'relaxation'
    }
    
    def __init__(self):
        self.s3_client = self._get_s3_client()
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    
    def _get_s3_client(self):
        """Создает S3 клиент для работы с R2"""
        return boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )
    
    def scan_r2_storage(self) -> List[R2FileInfo]:
        """
        Сканирует все файлы в R2 хранилище
        
        Returns:
            List[R2FileInfo]: Список всех файлов с метаданными
        """
        logger.info(f"🔍 Scanning R2 bucket: {self.bucket_name}")
        
        files = []
        paginator = self.s3_client.get_paginator('list_objects_v2')
        
        for page in paginator.paginate(Bucket=self.bucket_name):
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                key = obj['Key']
                
                # Пропускаем не-медиа файлы
                if not self._is_media_file(key):
                    continue
                
                file_info = self._parse_r2_file(obj)
                if file_info:
                    files.append(file_info)
        
        logger.info(f"📊 Found {len(files)} media files in R2")
        return files
    
    def _is_media_file(self, key: str) -> bool:
        """Проверяет, является ли файл медиа-файлом"""
        media_extensions = ('.mp4', '.mov', '.avi', '.jpg', '.jpeg', '.png', '.webp')
        return key.lower().endswith(media_extensions)
    
    def _parse_r2_file(self, obj: dict) -> Optional[R2FileInfo]:
        """
        Парсит информацию о файле из R2
        
        Ожидаемые форматы:
        - videos/exercises/main_001_technique_mentor.mp4
        - videos/motivation/weekly_mentor_week1.mp4  
        - images/avatars/mentor_avatar_1.jpg
        """
        key = obj['Key']
        parts = key.split('/')
        
        if len(parts) < 3:
            return None
            
        file_type = parts[0]  # videos или images
        category = parts[1]   # exercises, motivation, avatars, etc.
        filename = parts[-1]  # имя файла
        
        # Базовая информация
        file_info = R2FileInfo(
            key=key,
            size=obj['Size'],
            last_modified=obj['LastModified'].isoformat(),
            filename=filename,
            category=category
        )
        
        # Парсим exercise_id и метаданные для видео упражнений  
        if file_type == 'videos' and category == 'exercises':
            self._parse_exercise_video(file_info)
        elif file_type == 'images' and category == 'avatars':
            self._parse_avatar_image(file_info)
            
        return file_info
    
    def _parse_exercise_video(self, file_info: R2FileInfo):
        """
        Парсит видео упражнения: main_001_technique_mentor.mp4
        
        Формат: {exercise_id}_{video_type}_{archetype}.mp4
        """
        filename_without_ext = file_info.filename.rsplit('.', 1)[0]
        parts = filename_without_ext.split('_')
        
        if len(parts) >= 2:
            # Определяем exercise_id (первые 2 части: main_001)
            potential_exercise_parts = []
            for part in parts:
                if part.isdigit() or any(part.startswith(prefix.rstrip('_')) for prefix in self.EXERCISE_CATEGORIES.keys()):
                    potential_exercise_parts.append(part)
                else:
                    break
                    
            if len(potential_exercise_parts) >= 2:
                file_info.exercise_id = '_'.join(potential_exercise_parts)
                remaining_parts = parts[len(potential_exercise_parts):]
                
                # Ищем video_type и archetype в оставшихся частях
                for part in remaining_parts:
                    if part in self.VIDEO_TYPES:
                        file_info.video_type = part
                    elif part in self.ARCHETYPE_MAPPING:
                        file_info.archetype = self.ARCHETYPE_MAPPING[part]
    
    def _parse_avatar_image(self, file_info: R2FileInfo):
        """
        Парсит аватары: mentor_avatar_1.jpg
        
        Формат: {archetype}_avatar_{number}.jpg
        """
        filename_without_ext = file_info.filename.rsplit('.', 1)[0]
        parts = filename_without_ext.split('_')
        
        if len(parts) >= 2 and parts[0] in self.ARCHETYPE_MAPPING:
            file_info.archetype = self.ARCHETYPE_MAPPING[parts[0]]
    
    def extract_exercises_from_files(self, files: List[R2FileInfo]) -> Dict[str, Dict]:
        """
        Извлекает уникальные упражнения из файлов видео
        
        Returns:
            Dict[exercise_id, exercise_data]: Словарь упражнений для создания CSVExercise
        """
        exercises = {}
        
        for file_info in files:
            if file_info.exercise_id and file_info.category == 'exercises':
                exercise_id = file_info.exercise_id
                
                if exercise_id not in exercises:
                    # Генерируем название на основе ID
                    name_ru = self._generate_exercise_name(exercise_id)
                    
                    exercises[exercise_id] = {
                        'id': exercise_id,
                        'name_ru': name_ru,
                        'description': f'Упражнение {name_ru} (автоматически созданное из R2)',
                        'video_files': []
                    }
                
                exercises[exercise_id]['video_files'].append(file_info)
        
        logger.info(f"📋 Extracted {len(exercises)} unique exercises from R2")
        return exercises
    
    def _generate_exercise_name(self, exercise_id: str) -> str:
        """Генерирует читаемое название упражнения из ID"""
        # Простая генерация названий (можно расширить)
        name_mapping = {
            'warmup_': 'Разминка',
            'main_': 'Основное упражнение',
            'endurance_': 'Выносливость', 
            'relaxation_': 'Расслабление'
        }
        
        for prefix, base_name in name_mapping.items():
            if exercise_id.startswith(prefix):
                number = exercise_id.replace(prefix, '')
                return f"{base_name} {number}"
        
        return f"Упражнение {exercise_id}"
    
    def create_r2_video_data(self, files: List[R2FileInfo]) -> List[Dict]:
        """
        Создает данные для R2Video записей
        
        Returns:
            List[Dict]: Данные для создания R2Video объектов
        """
        r2_videos = []
        
        for file_info in files:
            if file_info.key.startswith('videos/'):
                # Код = имя файла без расширения  
                code = file_info.filename.rsplit('.', 1)[0]
                
                r2_video_data = {
                    'code': code,
                    'name': self._generate_video_name(file_info),
                    'description': f'Видео {code} (автоматически созданное из R2)',
                    'category': self._map_r2_category_to_model(file_info.category),
                    'archetype': self._map_archetype_to_model(file_info.archetype) if file_info.archetype else ''
                }
                
                r2_videos.append(r2_video_data)
        
        logger.info(f"🎥 Created {len(r2_videos)} R2Video records")
        return r2_videos
    
    def _generate_video_name(self, file_info: R2FileInfo) -> str:
        """Генерирует читаемое название видео"""
        if file_info.exercise_id and file_info.video_type:
            exercise_name = self._generate_exercise_name(file_info.exercise_id)
            type_name = {
                'instruction': 'инструкция',
                'technique': 'техника',
                'mistake': 'ошибки',
                'reminder': 'напоминание',
                'motivation': 'мотивация'
            }.get(file_info.video_type, file_info.video_type)
            
            return f"{exercise_name} - {type_name}"
        
        return file_info.filename.rsplit('.', 1)[0].replace('_', ' ').title()
    
    def _map_r2_category_to_model(self, r2_category: str) -> str:
        """Маппит категории из R2 в модель R2Video"""
        mapping = {
            'exercises': 'exercises',
            'motivation': 'motivation',
            'final': 'final',
            'progress': 'progress',
            'weekly': 'weekly'
        }
        return mapping.get(r2_category, 'exercises')
    
    def _map_archetype_to_model(self, archetype: str) -> str:
        """Маппит архетипы в модель R2Video"""
        if not archetype:
            return ''
        return archetype  # mentor, professional, peer уже в нужном формате