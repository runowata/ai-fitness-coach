#!/usr/bin/env python3
"""
Management command to analyze R2 video structure and categorize all videos
"""

import os
import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Analyze R2 video structure and categorize all available videos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed breakdown of each category'
        )

    def handle(self, *args, **options):
        self.detailed = options['detailed']

        self.stdout.write("🔍 АНАЛИЗ СТРУКТУРЫ ВИДЕО В R2")
        self.stdout.write("=" * 50)
        
        # Get S3 client
        try:
            s3_client = self._get_s3_client()
        except Exception as e:
            raise CommandError(f"Failed to create S3 client: {e}")
        
        # Discover all videos
        self.stdout.write("📂 Сканирование всех видео в R2...")
        all_videos = self._discover_all_videos(s3_client)
        
        if not all_videos:
            self.stdout.write(self.style.WARNING("No videos found in R2"))
            return
        
        # Analyze structure
        categories = self._categorize_videos(all_videos)
        
        # Show results
        self._show_analysis(categories, all_videos)

    def _get_s3_client(self):
        """Create S3 client for R2"""
        endpoint_url = os.getenv('R2_ENDPOINT') or os.getenv('AWS_S3_ENDPOINT_URL')
        
        return boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            config=Config(signature_version='s3v4', retries={'max_attempts': 3}),
            region_name='auto'
        )

    def _discover_all_videos(self, s3_client) -> List[Tuple[str, int]]:
        """Discover ALL video files in R2 bucket"""
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.MP4', '.MOV'}
        video_files = []
        
        try:
            bucket_name = os.getenv('R2_BUCKET', 'ai-fitness-media')
            paginator = s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=bucket_name):
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    key = obj['Key']
                    
                    # Check if it's a video file
                    if any(key.endswith(ext) for ext in video_extensions):
                        video_files.append((key, obj['Size']))
            
        except ClientError as e:
            raise CommandError(f"Failed to list R2 objects: {e}")
        
        self.stdout.write(f"Найдено {len(video_files)} видео файлов")
        return video_files

    def _categorize_videos(self, videos: List[Tuple[str, int]]) -> Dict:
        """Categorize videos by structure and type"""
        
        categories = {
            'closing': [],           # videos/closing/
            'intro': [],            # videos/intro/ (if exists)
            'exercises_technique': [],  # exercises/*_technique_*
            'exercises_mistake': [],    # exercises/*_mistake_*  
            'exercises_explain': [],    # exercises/*_explain_*
            'exercises_final': [],     # exercises/final_*
            'exercises_other': [],     # other exercise files
            'motivational': [],        # weekly/motivation videos
            'instructions': [],        # instruction videos
            'reminders': [],          # reminder videos
            'other': []               # uncategorized
        }
        
        # Patterns for categorization
        patterns = {
            r'videos/closing/': 'closing',
            r'videos/intro/': 'intro', 
            r'videos/exercises/.*_technique_': 'exercises_technique',
            r'videos/exercises/.*_mistake_': 'exercises_mistake',
            r'videos/exercises/.*_explain_': 'exercises_explain',
            r'videos/exercises/final_': 'exercises_final',
            r'videos/motivation/': 'motivational',
            r'videos/weekly/': 'motivational',
            r'videos/instructions/': 'instructions',
            r'videos/reminders/': 'reminders',
        }
        
        for video_path, size in videos:
            categorized = False
            
            for pattern, category in patterns.items():
                if re.search(pattern, video_path):
                    categories[category].append((video_path, size))
                    categorized = True
                    break
            
            if not categorized:
                if 'exercises/' in video_path:
                    categories['exercises_other'].append((video_path, size))
                else:
                    categories['other'].append((video_path, size))
        
        return categories

    def _show_analysis(self, categories: Dict, all_videos: List):
        """Show detailed analysis of video structure"""
        
        self.stdout.write("\n📊 АНАЛИЗ КАТЕГОРИЙ ВИДЕО")
        self.stdout.write("=" * 40)
        
        total_size = sum(size for _, size in all_videos)
        
        for category, videos in categories.items():
            if not videos:
                continue
                
            count = len(videos)
            category_size = sum(size for _, size in videos)
            size_gb = category_size / (1024**3)
            
            self.stdout.write(f"\n📁 {category.upper()}:")
            self.stdout.write(f"   Количество: {count}")
            self.stdout.write(f"   Размер: {size_gb:.2f} GB")
            
            if self.detailed and count <= 20:
                self.stdout.write("   Файлы:")
                for path, size in videos[:10]:  # Show first 10
                    filename = path.split('/')[-1]
                    size_mb = size / (1024**2)
                    self.stdout.write(f"     • {filename} ({size_mb:.1f} MB)")
                if count > 10:
                    self.stdout.write(f"     ... и еще {count - 10} файлов")
        
        # Identify potential exercises
        self._analyze_exercises(categories)
        
        # Check for missing video types
        self._check_missing_types(categories)
        
        # Summary
        self.stdout.write(f"\n📈 ИТОГО:")
        self.stdout.write(f"   Всего видео: {len(all_videos)}")
        self.stdout.write(f"   Общий размер: {total_size / (1024**3):.2f} GB")

    def _analyze_exercises(self, categories: Dict):
        """Analyze what exercises we have videos for"""
        self.stdout.write(f"\n🏋️ АНАЛИЗ УПРАЖНЕНИЙ:")
        
        # Extract exercise names from technique/mistake videos
        exercise_names = set()
        
        for video_path, _ in categories['exercises_technique']:
            # Extract exercise name from path like: videos/exercises/push-ups_technique_m01.mp4
            filename = video_path.split('/')[-1]
            match = re.match(r'(.+?)_technique_', filename)
            if match:
                exercise_names.add(match.group(1))
        
        for video_path, _ in categories['exercises_mistake']:
            filename = video_path.split('/')[-1]
            match = re.match(r'(.+?)_mistake_', filename)
            if match:
                exercise_names.add(match.group(1))
        
        self.stdout.write(f"   Упражнений с technique/mistake видео: {len(exercise_names)}")
        
        if self.detailed and exercise_names:
            self.stdout.write("   Примеры упражнений:")
            for exercise in sorted(list(exercise_names))[:15]:
                self.stdout.write(f"     • {exercise}")
            if len(exercise_names) > 15:
                self.stdout.write(f"     ... и еще {len(exercise_names) - 15}")

    def _check_missing_types(self, categories: Dict):
        """Check for missing video types based on our VideoKind constants"""
        self.stdout.write(f"\n⚠️  ПРОВЕРКА ПОКРЫТИЯ:")
        
        expected_types = {
            'intro': categories['intro'],
            'closing': categories['closing'], 
            'technique': categories['exercises_technique'],
            'mistake': categories['exercises_mistake'],
            'instruction': categories['instructions'],
            'reminder': categories['reminders'],
            'weekly/motivation': categories['motivational']
        }
        
        missing_types = []
        present_types = []
        
        for video_type, videos in expected_types.items():
            if videos:
                present_types.append(f"{video_type} ({len(videos)})")
            else:
                missing_types.append(video_type)
        
        if present_types:
            self.stdout.write("   ✅ Найденные типы: " + ", ".join(present_types))
        
        if missing_types:
            self.stdout.write("   ❌ Отсутствующие типы: " + ", ".join(missing_types))
        else:
            self.stdout.write("   ✅ Все основные типы видео присутствуют!")
        
        # Check for archetype-specific videos
        self._check_archetype_coverage(categories)

    def _check_archetype_coverage(self, categories: Dict):
        """Check if we have archetype-specific videos"""
        self.stdout.write(f"\n🎭 ПРОВЕРКА АРХЕТИПОВ:")
        
        archetype_patterns = {
            'mentor': ['mentor', 'мудрый', 'наставник'],
            'professional': ['professional', 'профессионал', 'деловой'], 
            'peer': ['peer', 'ровесник', 'бро', 'друг']
        }
        
        archetype_counts = defaultdict(int)
        
        # Check all video paths for archetype indicators
        all_videos = []
        for videos in categories.values():
            all_videos.extend(videos)
        
        for video_path, _ in all_videos:
            filename = video_path.lower()
            for archetype, keywords in archetype_patterns.items():
                if any(keyword in filename for keyword in keywords):
                    archetype_counts[archetype] += 1
        
        if archetype_counts:
            self.stdout.write("   Видео по архетипам:")
            for archetype, count in archetype_counts.items():
                self.stdout.write(f"     • {archetype}: {count} видео")
        else:
            self.stdout.write("   ⚠️  Архетип-специфичные видео не обнаружены")
            self.stdout.write("     Возможно, нужно добавить логику группировки по архетипам")