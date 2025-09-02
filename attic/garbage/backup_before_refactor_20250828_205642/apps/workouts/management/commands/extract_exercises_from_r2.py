#!/usr/bin/env python3
"""
Management command to extract exercises from R2 videos and create CSVExercise records
"""

import os
import re
from typing import Dict, Set

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.workouts.models import CSVExercise


class Command(BaseCommand):
    help = 'Extract exercises from R2 video filenames and create CSVExercise records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Update existing exercises if they exist'
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.force = options['force']

        self.stdout.write("🏋️ ИЗВЛЕЧЕНИЕ УПРАЖНЕНИЙ ИЗ R2 ВИДЕО")
        self.stdout.write("=" * 50)
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        # Get S3 client
        try:
            s3_client = self._get_s3_client()
        except Exception as e:
            raise CommandError(f"Failed to create S3 client: {e}")
        
        # Extract exercises from R2 video structure
        self.stdout.write("📂 Сканирование видео для извлечения упражнений...")
        exercise_names = self._extract_exercise_names(s3_client)
        
        if not exercise_names:
            self.stdout.write(self.style.WARNING("No exercises found in R2 videos"))
            return
        
        self.stdout.write(f"Найдено {len(exercise_names)} уникальных упражнений")
        
        # Create CSVExercise records
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for exercise_name in sorted(exercise_names):
            try:
                result = self._create_or_update_exercise(exercise_name)
                
                if result == 'created':
                    created_count += 1
                elif result == 'updated':
                    updated_count += 1
                elif result == 'skipped':
                    skipped_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing {exercise_name}: {e}")
                )
        
        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("📊 SUMMARY")
        self.stdout.write(f"   Created: {created_count}")
        self.stdout.write(f"   Updated: {updated_count}")
        self.stdout.write(f"   Skipped: {skipped_count}")
        self.stdout.write(f"   Total:   {len(exercise_names)}")

    def _get_s3_client(self):
        """Create S3 client for R2"""
        from django.conf import settings

        # Use Django settings for consistency
        config = Config(
            signature_version='s3v4', 
            retries={'max_attempts': 3},
            s3={'addressing_style': 'virtual'}  # критично для R2
        )
        
        return boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=config,
            region_name=settings.AWS_S3_REGION_NAME
        )

    def _extract_exercise_names(self, s3_client) -> Set[str]:
        """Extract unique exercise names from R2 video filenames"""
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.MP4', '.MOV'}
        exercise_names = set()
        
        try:
            bucket_name = os.getenv('R2_BUCKET', 'ai-fitness-media')
            paginator = s3_client.get_paginator('list_objects_v2')
            
            # Focus on exercise videos
            for page in paginator.paginate(Bucket=bucket_name, Prefix='videos/exercises/'):
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    key = obj['Key']
                    
                    # Check if it's a video file
                    if any(key.endswith(ext) for ext in video_extensions):
                        exercise_name = self._parse_exercise_name_from_filename(key)
                        if exercise_name:
                            exercise_names.add(exercise_name)
                            
        except ClientError as e:
            raise CommandError(f"Failed to list R2 objects: {e}")
        
        return exercise_names

    def _parse_exercise_name_from_filename(self, filename: str) -> str:
        """Parse exercise name from R2 video filename"""
        
        # Extract filename from path
        basename = filename.split('/')[-1]
        
        # Patterns to extract exercise names
        patterns = [
            # Standard patterns: exercise_type_model.ext
            r'([a-zA-Z-]+)_(technique|mistake|explain)_',
            # Alternative patterns  
            r'([a-zA-Z-]+)_(m\d+)\.', 
        ]
        
        for pattern in patterns:
            match = re.match(pattern, basename)
            if match:
                exercise_name = match.group(1)
                
                # Clean up exercise name
                exercise_name = exercise_name.lower()
                exercise_name = exercise_name.replace('_', '-')
                
                # Skip obviously non-exercise names
                skip_patterns = [
                    r'^final',
                    r'^\d{4}-',  # dates  
                    r'^img\d+',  # image files
                    r'^video',   # generic video names
                    r'^storysaver',
                    r'chaturbate',
                    r'onlyfans',
                    r'igor-nude',
                    r'alex-animal',
                    r'dmitry-averyano',
                    r'russian-',
                    r'vladifbb',
                    r'young-',
                    r'-explain',
                    r'casting',
                    r'deepthroat',
                    r'drilling',
                    r'jerking',
                    r'lust-',
                    r'passion',
                    r'wanna',
                    r'want-',
                    r'need-',
                    r'.*-cum',
                    r'addicted',
                    r'muscle-russia',
                    r'training-o',
                    r'pride-festiv',
                    r'^-',  # Names starting with dash
                ]
                
                if any(re.search(skip, exercise_name) for skip in skip_patterns):
                    continue
                
                # Only return if it looks like an exercise name
                if len(exercise_name) >= 3 and re.match(r'^[a-z-]+$', exercise_name):
                    return exercise_name
        
        return None

    def _create_or_update_exercise(self, exercise_name: str) -> str:
        """Create or update CSVExercise record"""
        
        if self.dry_run:
            existing = CSVExercise.objects.filter(id=exercise_name).first()
            action = 'UPDATE' if existing else 'CREATE'
            self.stdout.write(f"  [DRY RUN] Would {action}: {exercise_name}")
            return 'created' if not existing else 'updated'
        
        # Check if exercise already exists
        existing_exercise = CSVExercise.objects.filter(id=exercise_name).first()
        
        if existing_exercise and not self.force:
            self.stdout.write(f"  Skipped: {exercise_name} (already exists)")
            return 'skipped'
        
        # Infer exercise properties from name
        properties = self._infer_exercise_properties(exercise_name)
        
        exercise_data = {
            'id': exercise_name,
            'name_ru': self._format_exercise_name(exercise_name),
            'name_en': self._format_exercise_name(exercise_name),
            'level': properties['difficulty'],
            'description': f'Exercise: {self._format_exercise_name(exercise_name)}',
            'muscle_group': properties['primary_muscle_group'],
            'exercise_type': properties['exercise_type'],
            'ai_tags': properties['ai_tags'],
            'is_active': True,
        }
        
        with transaction.atomic():
            if existing_exercise:
                # Update existing exercise
                for field, value in exercise_data.items():
                    if field != 'id':  # Don't update primary key
                        setattr(existing_exercise, field, value)
                existing_exercise.save()
                
                self.stdout.write(self.style.SUCCESS(f"  Updated: {exercise_name}"))
                return 'updated'
            else:
                # Create new exercise
                exercise = CSVExercise.objects.create(**exercise_data)
                self.stdout.write(self.style.SUCCESS(f"  Created: {exercise_name} -> {exercise.name_ru}"))
                return 'created'

    def _format_exercise_name(self, slug: str) -> str:
        """Convert slug to human-readable name"""
        # Convert slug to title case
        words = slug.split('-')
        formatted_words = []
        
        for word in words:
            # Handle special cases
            special_cases = {
                'ups': 'Ups',
                'deadlifts': 'Deadlifts', 
                'squats': 'Squats',
                'curls': 'Curls',
                'press': 'Press',
                'rows': 'Rows',
                'flyes': 'Flyes',
                'raises': 'Raises',
                'extensions': 'Extensions',
                'pushdowns': 'Pushdowns',
                'pulls': 'Pulls',
            }
            
            if word in special_cases:
                formatted_words.append(special_cases[word])
            else:
                formatted_words.append(word.capitalize())
        
        return ' '.join(formatted_words)

    def _infer_exercise_properties(self, exercise_name: str) -> Dict:
        """Infer exercise properties from name"""
        
        # Define patterns for muscle groups
        muscle_group_patterns = {
            'chest': ['chest', 'press', 'bench', 'flyes', 'push-ups', 'dips'],
            'back': ['rows', 'pull-ups', 'chin-ups', 'deadlift', 'shrugs'],
            'shoulders': ['shoulder', 'raises', 'overhead', 'lateral', 'front', 'rear'],
            'arms': ['curls', 'extensions', 'pushdowns', 'bicep', 'tricep'],
            'legs': ['squats', 'lunges', 'leg', 'cal', 'glute', 'hip'],
            'core': ['crunches', 'plank', 'abs', 'russian', 'bicycle', 'mountain'],
            'full_body': ['burpees', 'jump', 'bear', 'crawls', 'star'],
        }
        
        # Equipment patterns
        equipment_patterns = {
            'dumbbell': ['dumbbell'],
            'barbell': ['barbell'],
            'kettlebell': ['kettlebell'],
            'cable': ['cable'],
            'bodyweight': ['push-ups', 'pull-ups', 'squats', 'lunges', 'plank', 'crunches', 'dips'],
            'medicine_ball': ['medicine', 'ball'],
            'battle_ropes': ['battle', 'ropes'],
            'box': ['box', 'step'],
        }
        
        # Difficulty patterns
        difficulty_patterns = {
            'advanced': ['handstand', 'pistol', 'archer', 'one-arm', 'single-arm', 'explosive'],
            'intermediate': ['bulgarian', 'deficit', 'decline', 'incline'],
            'beginner': ['knee', 'assisted', 'wall'],
        }
        
        # Determine primary muscle group (simplified in Phase 5.6)
        primary_muscle_group = 'full_body'  # default
        
        for muscle_group, patterns in muscle_group_patterns.items():
            if any(pattern in exercise_name for pattern in patterns):
                if muscle_group != 'full_body':  # Prefer specific groups
                    primary_muscle_group = muscle_group
                    break
        
        # Determine difficulty
        difficulty = 'intermediate'  # default
        
        for diff, patterns in difficulty_patterns.items():
            if any(pattern in exercise_name for pattern in patterns):
                difficulty = diff
                break
        
        # Determine exercise type
        exercise_type = 'strength'  # default
        if any(pattern in exercise_name for pattern in ['jump', 'run', 'jack', 'burpee', 'mountain']):
            exercise_type = 'cardio'
        elif any(pattern in exercise_name for pattern in ['stretch', 'yoga']):
            exercise_type = 'stretch'
        
        # Create AI tags for the exercise (simplified in Phase 5.6)
        ai_tags = [primary_muscle_group, difficulty, exercise_type]
        
        return {
            'primary_muscle_group': primary_muscle_group,
            'difficulty': difficulty,
            'exercise_type': exercise_type,
            'ai_tags': list(set(ai_tags))  # Remove duplicates
        }