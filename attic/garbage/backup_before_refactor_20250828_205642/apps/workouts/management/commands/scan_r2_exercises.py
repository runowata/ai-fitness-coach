#!/usr/bin/env python3
"""
Management command to scan R2 storage and rebuild exercise database
based on actual video files structure.
"""

import re
import logging
from collections import defaultdict
from typing import Dict, List, Set, Tuple

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.workouts.models import CSVExercise, VideoClip
from apps.workouts.constants import VideoKind, Archetype

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Scan R2 storage and rebuild exercise database based on actual video files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes',
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing CSVExercise and VideoClip records before rebuilding',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.verbose = options['verbose']
        self.clear_existing = options['clear_existing']
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made'))
        
        try:
            # Connect to R2
            s3_client = self._get_r2_client()
            
            # Scan R2 storage
            self.stdout.write('📡 Scanning R2 storage...')
            video_structure = self._scan_r2_videos(s3_client)
            
            # Analyze structure
            self._analyze_video_structure(video_structure)
            
            # Build exercise database
            if not self.dry_run:
                with transaction.atomic():
                    self._rebuild_database(video_structure)
            
            self.stdout.write(self.style.SUCCESS('✅ R2 scan completed successfully'))
            
        except Exception as e:
            logger.error(f"R2 scan failed: {e}")
            raise CommandError(f'R2 scan failed: {e}')

    def _get_r2_client(self):
        """Initialize R2 S3 client"""
        try:
            # Try environment variables first, then hardcoded values from upload script
            access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None) or '3a9fd5a6b38ec994e057e33c1096874e'
            secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None) or '0817f9a3154b63b1968620a966e05e36f80fca0308ba91d9c8bf65e8622baa13'
            endpoint_url = getattr(settings, 'AWS_S3_ENDPOINT_URL', None) or 'https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com'
            
            return boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name='auto'  # R2 uses 'auto' region
            )
        except Exception as e:
            raise CommandError(f'Failed to connect to R2: {e}')

    def _scan_r2_videos(self, s3_client) -> Dict:
        """Scan all video files in R2 storage"""
        bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None) or 'ai-fitness-media'
        video_structure = defaultdict(lambda: defaultdict(list))
        
        try:
            paginator = s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=bucket_name, Prefix='videos/'):
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    key = obj['Key']
                    
                    # Skip directories
                    if key.endswith('/'):
                        continue
                    
                    # Parse video file path
                    parsed = self._parse_video_path(key)
                    if parsed:
                        category, exercise_slug, video_kind, archetype, model = parsed
                        video_structure[category][exercise_slug].append({
                            'key': key,
                            'video_kind': video_kind,
                            'archetype': archetype,
                            'model': model,
                            'size': obj['Size']
                        })
                        
                        if self.verbose:
                            self.stdout.write(f"  Found: {exercise_slug} | {video_kind} | {archetype}")
            
            return dict(video_structure)
            
        except Exception as e:
            raise CommandError(f'Failed to scan R2: {e}')

    def _parse_video_path(self, path: str) -> Tuple[str, str, str, str, str] or None:
        """
        Parse R2 video file path into components
        
        Expected formats:
        - videos/exercises/{exercise}_technique_{model}.mp4
        - videos/exercises/{exercise}_mistake_{model}.mp4  
        - videos/instructions/{exercise}_instruction_{archetype}_{model}.mp4
        - videos/reminders/{exercise}_reminder_{archetype}_{number}.mp4
        - videos/motivation/weekly_{archetype}_week{number}.mp4
        """
        
        # Remove videos/ prefix and file extension
        if not path.startswith('videos/'):
            return None
            
        path = path[7:]  # Remove 'videos/'
        name, ext = path.rsplit('.', 1)
        
        if ext.lower() not in ['mp4', 'mov', 'mkv', 'avi']:
            return None
        
        parts = path.split('/')
        if len(parts) < 2:
            return None
            
        category = parts[0]  # exercises, instructions, reminders, etc.
        filename = parts[-1].rsplit('.', 1)[0]  # Remove extension
        
        # Parse based on category
        if category == 'exercises':
            if '/explain/' in path:
                # videos/exercises/explain/{exercise}_explain_{model}.mp4
                match = re.match(r'(.+)_explain_(.+)', filename)
                if match:
                    exercise_slug, model = match.groups()
                    return ('exercises', exercise_slug, 'explain', '', model)
            else:
                # videos/exercises/{exercise}_{technique|mistake}_{model}.mp4
                match = re.match(r'(.+)_(technique|mistake)_(.+)', filename)
                if match:
                    exercise_slug, video_kind, model = match.groups()
                    return ('exercises', exercise_slug, video_kind, '', model)
        
        elif category == 'instructions':
            # videos/instructions/{exercise}_instruction_{archetype}_{model}.mp4
            match = re.match(r'(.+)_instruction_(.+)_(.+)', filename)
            if match:
                exercise_slug, archetype, model = match.groups()
                # Normalize archetype names
                archetype = self._normalize_archetype(archetype)
                return ('instructions', exercise_slug, 'instruction', archetype, model)
        
        elif category == 'reminders':
            # videos/reminders/{exercise}_reminder_{archetype}_{number}.mp4
            match = re.match(r'(.+)_reminder_(.+)_(\d+)', filename)
            if match:
                exercise_slug, archetype, number = match.groups()
                archetype = self._normalize_archetype(archetype)
                return ('reminders', exercise_slug, 'reminder', archetype, f'r{number}')
        
        elif category == 'motivation':
            # videos/motivation/weekly_{archetype}_week{number}.mp4
            match = re.match(r'weekly_(.+)_week(\d+)', filename)
            if match:
                archetype, week_num = match.groups()
                archetype = self._normalize_archetype(archetype)
                return ('motivation', f'weekly_w{week_num}', 'weekly', archetype, 'v1')
        
        # Log unmatched patterns for debugging
        if self.verbose:
            self.stdout.write(f"  ⚠️  Unmatched: {path}")
        
        return None

    def _normalize_archetype(self, archetype_name: str) -> str:
        """Normalize archetype name to standard format"""
        archetype_map = {
            'best_mate': 'peer',
            'pro_coach': 'professional',
            'wise_mentor': 'mentor',
            'peer': 'peer',
            'professional': 'professional', 
            'mentor': 'mentor'
        }
        return archetype_map.get(archetype_name.lower(), archetype_name.lower())

    def _analyze_video_structure(self, video_structure: Dict):
        """Analyze and report video structure statistics"""
        self.stdout.write('\n📊 VIDEO STRUCTURE ANALYSIS')
        self.stdout.write('=' * 50)
        
        total_exercises = set()
        total_videos = 0
        
        for category, exercises in video_structure.items():
            category_videos = sum(len(videos) for videos in exercises.values())
            total_videos += category_videos
            total_exercises.update(exercises.keys())
            
            self.stdout.write(f'\n{category.upper()}:')
            self.stdout.write(f'  Exercises: {len(exercises)}')
            self.stdout.write(f'  Videos: {category_videos}')
            
            if self.verbose:
                for exercise_slug, videos in sorted(exercises.items())[:5]:
                    kinds = set(v['video_kind'] for v in videos)
                    archetypes = set(v['archetype'] for v in videos if v['archetype'])
                    self.stdout.write(f'    {exercise_slug}: {len(videos)} videos ({", ".join(kinds)})')
                
                if len(exercises) > 5:
                    self.stdout.write(f'    ... and {len(exercises) - 5} more')
        
        self.stdout.write(f'\n📈 TOTALS:')
        self.stdout.write(f'  Unique exercises: {len(total_exercises)}')
        self.stdout.write(f'  Total videos: {total_videos}')
        
        # Exercise code analysis
        code_exercises = [ex for ex in total_exercises if self._is_exercise_code(ex)]
        slug_exercises = [ex for ex in total_exercises if not self._is_exercise_code(ex)]
        
        self.stdout.write(f'  Code format (WZ001, EX001, etc): {len(code_exercises)}')
        self.stdout.write(f'  Slug format (push-ups, etc): {len(slug_exercises)}')
        
        if self.verbose and slug_exercises:
            self.stdout.write(f'\nSlug examples: {slug_exercises[:10]}')

    def _is_exercise_code(self, exercise_slug: str) -> bool:
        """Check if exercise slug matches code pattern (WZ001, EX001, etc)"""
        return bool(re.match(r'^[A-Z]{2}\d{3}(_v\d+)?$', exercise_slug))

    def _rebuild_database(self, video_structure: Dict):
        """Rebuild CSVExercise and VideoClip models based on R2 structure"""
        self.stdout.write('\n🔨 REBUILDING DATABASE')
        self.stdout.write('=' * 50)
        
        if self.clear_existing:
            self.stdout.write('🗑️  Clearing existing records...')
            VideoClip.objects.all().delete()
            CSVExercise.objects.all().delete()
            
        # Extract all unique exercises
        all_exercises = set()
        for category_exercises in video_structure.values():
            all_exercises.update(category_exercises.keys())
        
        # Create CSVExercise records
        self.stdout.write(f'📝 Creating {len(all_exercises)} CSVExercise records...')
        created_exercises = 0
        
        for exercise_slug in sorted(all_exercises):
            # Skip motivation/weekly entries - they're not exercises
            if exercise_slug.startswith('weekly_'):
                continue
                
            # Convert slug to exercise code  
            exercise_code = self._convert_to_exercise_code(exercise_slug)
            
            # Determine exercise category from slug
            category = self._categorize_exercise(exercise_slug)
            
            # Create exercise record
            exercise, created = CSVExercise.objects.get_or_create(
                id=exercise_code,
                defaults={
                    'name_ru': self._generate_exercise_name(exercise_slug),
                    'name_en': exercise_slug.replace('-', ' ').title(),
                    'level': 'intermediate',  # Default level
                    'exercise_type': category,
                    'muscle_group': self._infer_muscle_group(exercise_slug),
                    'is_active': True
                }
            )
            
            if created:
                created_exercises += 1
                
        self.stdout.write(f'✅ Created {created_exercises} new exercises')
        
        # Create VideoClip records
        self.stdout.write('🎬 Creating VideoClip records...')
        created_clips = 0
        
        for category, exercises in video_structure.items():
            for exercise_slug, videos in exercises.items():
                # Skip weekly motivation videos - different structure
                if exercise_slug.startswith('weekly_'):
                    continue
                    
                # Convert slug to exercise code
                exercise_code = self._convert_to_exercise_code(exercise_slug)
                
                try:
                    exercise = CSVExercise.objects.get(id=exercise_code)
                except CSVExercise.DoesNotExist:
                    self.stdout.write(f'⚠️  Exercise not found: {exercise_slug}')
                    continue
                
                for video in videos:
                    # Create VideoClip record
                    clip, created = VideoClip.objects.get_or_create(
                        exercise=exercise,
                        r2_kind=video['video_kind'],
                        archetype=video['archetype'],
                        model_name=video['model'],
                        defaults={
                            'r2_file': video['key'],
                            'duration_seconds': 30,  # Default duration
                            'provider': 'r2',
                            'is_active': True
                        }
                    )
                    
                    if created:
                        created_clips += 1
        
        self.stdout.write(f'✅ Created {created_clips} new video clips')

    def _categorize_exercise(self, exercise_slug: str) -> str:
        """Categorize exercise based on slug pattern"""
        if exercise_slug.startswith('WZ'):
            return 'mobility'
        elif exercise_slug.startswith('EX'):
            return 'strength'  
        elif exercise_slug.startswith('SX'):
            return 'cardio'
        elif exercise_slug.startswith('CZ') or exercise_slug.startswith('CX'):
            return 'flexibility'
        else:
            # Map R2 slug categories to exercise types
            if exercise_slug.startswith('warmup_'):
                return 'mobility'
            elif exercise_slug.startswith('main_'):
                return 'strength'
            elif exercise_slug.startswith('endurance_'):
                return 'cardio'
            elif exercise_slug.startswith('relaxation_'):
                return 'flexibility'
            else:
                # Fallback inference
                slug_lower = exercise_slug.lower()
                if any(word in slug_lower for word in ['stretch', 'mobility', 'foam', 'roll', 'relax']):
                    return 'flexibility'
                elif any(word in slug_lower for word in ['run', 'jump', 'cardio', 'hiit', 'burpee', 'endurance']):
                    return 'cardio'
                else:
                    return 'strength'

    def _convert_to_exercise_code(self, exercise_slug: str) -> str:
        """Convert R2 slug to standard exercise code format"""
        if exercise_slug.startswith('warmup_'):
            # warmup_01 -> WZ001
            number = exercise_slug.split('_')[1].zfill(3)
            return f'WZ{number}'
        elif exercise_slug.startswith('main_'):
            # main_001 -> EX001
            number = exercise_slug.split('_')[1].zfill(3)
            return f'EX{number}'
        elif exercise_slug.startswith('endurance_'):
            # endurance_01 -> SX001
            number = exercise_slug.split('_')[1].zfill(3)
            return f'SX{number}'
        elif exercise_slug.startswith('relaxation_'):
            # relaxation_01 -> CZ001
            number = exercise_slug.split('_')[1].zfill(3)
            return f'CZ{number}'
        else:
            # Keep as-is for non-standard slugs
            return exercise_slug

    def _generate_exercise_name(self, exercise_slug: str) -> str:
        """Generate Russian exercise name from slug"""
        # Basic slug to name conversion
        name = exercise_slug.replace('-', ' ').replace('_', ' ')
        
        # Simple translation map for common exercises
        translations = {
            'push ups': 'Отжимания',
            'pull ups': 'Подтягивания', 
            'squats': 'Приседания',
            'plank': 'Планка',
            'jumping jacks': 'Прыжки на месте',
            'burpees': 'Берпи',
            'lunges': 'Выпады',
            'deadlift': 'Становая тяга',
            'bench press': 'Жим лежа'
        }
        
        return translations.get(name.lower(), name.title())

    def _infer_muscle_group(self, exercise_slug: str) -> str:
        """Infer muscle group from exercise slug"""
        slug_lower = exercise_slug.lower()
        
        if any(word in slug_lower for word in ['chest', 'bench', 'push']):
            return 'Грудь'
        elif any(word in slug_lower for word in ['back', 'pull', 'row']):
            return 'Спина'
        elif any(word in slug_lower for word in ['squat', 'lunge', 'leg']):
            return 'Ноги'
        elif any(word in slug_lower for word in ['shoulder', 'press']):
            return 'Плечи'
        elif any(word in slug_lower for word in ['arm', 'bicep', 'tricep', 'curl']):
            return 'Руки'
        elif any(word in slug_lower for word in ['core', 'plank', 'crunch']):
            return 'Пресс'
        else:
            return 'Все тело'