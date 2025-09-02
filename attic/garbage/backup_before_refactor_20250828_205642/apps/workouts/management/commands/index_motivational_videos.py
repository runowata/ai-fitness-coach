#!/usr/bin/env python3
"""
Management command to scan and index motivational videos from R2 storage
by trainer archetypes, categorizing them as daily, weekly, bi-weekly, and completion videos.
"""

import boto3
import json
import logging
from collections import defaultdict
from typing import Dict, List, Tuple

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.workouts.models import VideoClip, WeeklyLesson, FinalVideo
from apps.workouts.constants import VideoKind, Archetype

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Index motivational videos from R2 storage by trainer archetypes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be indexed without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.verbose = options['verbose']
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made'))
        
        try:
            # Connect to R2
            s3_client = self._get_r2_client()
            
            # Scan motivational videos
            self.stdout.write('📡 Scanning motivational videos in R2...')
            motivational_structure = self._scan_motivational_videos(s3_client)
            
            # Analyze structure
            self._analyze_motivational_structure(motivational_structure)
            
            # Index videos in database
            if not self.dry_run:
                with transaction.atomic():
                    self._index_motivational_videos(motivational_structure)
            
            self.stdout.write(self.style.SUCCESS('✅ Motivational video indexing completed'))
            
        except Exception as e:
            logger.error(f"Motivational video indexing failed: {e}")
            raise CommandError(f'Indexing failed: {e}')

    def _get_r2_client(self):
        """Initialize R2 S3 client"""
        try:
            # Use hardcoded values from upload script for compatibility
            access_key = '3a9fd5a6b38ec994e057e33c1096874e'
            secret_key = '0817f9a3154b63b1968620a966e05e36f80fca0308ba91d9c8bf65e8622baa13'
            endpoint_url = 'https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com'
            
            return boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name='auto'
            )
        except Exception as e:
            raise CommandError(f'Failed to connect to R2: {e}')

    def _scan_motivational_videos(self, s3_client) -> Dict:
        """Scan motivational video files in R2 storage"""
        bucket_name = 'ai-fitness-media'
        motivational_structure = defaultdict(lambda: defaultdict(list))
        
        try:
            paginator = s3_client.get_paginator('list_objects_v2')
            
            # Scan videos/motivation/ folder
            for page in paginator.paginate(Bucket=bucket_name, Prefix='videos/motivation/'):
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    key = obj['Key']
                    
                    # Skip directories
                    if key.endswith('/'):
                        continue
                    
                    # Parse motivational video path
                    parsed = self._parse_motivational_path(key)
                    if parsed:
                        video_type, archetype, identifier, trainer_name = parsed
                        motivational_structure[video_type][archetype].append({
                            'key': key,
                            'identifier': identifier,
                            'trainer_name': trainer_name,
                            'size': obj['Size']
                        })
                        
                        if self.verbose:
                            self.stdout.write(f"  Found: {video_type} | {archetype} | {identifier}")
            
            # Also scan videos/speech/ folder for additional motivational content
            for page in paginator.paginate(Bucket=bucket_name, Prefix='videos/speech/'):
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    key = obj['Key']
                    
                    if key.endswith('/'):
                        continue
                    
                    parsed = self._parse_speech_path(key)
                    if parsed:
                        video_type, archetype, identifier, trainer_name = parsed
                        motivational_structure[video_type][archetype].append({
                            'key': key,
                            'identifier': identifier,
                            'trainer_name': trainer_name,
                            'size': obj['Size']
                        })
                        
                        if self.verbose:
                            self.stdout.write(f"  Found speech: {video_type} | {archetype} | {identifier}")
            
            return dict(motivational_structure)
            
        except Exception as e:
            raise CommandError(f'Failed to scan R2 motivational videos: {e}')

    def _parse_motivational_path(self, path: str) -> Tuple[str, str, str, str] or None:
        """
        Parse motivational video file path into components
        
        Actual R2 formats found:
        - videos/motivation/intro_{archetype}_day{XX}.mp4
        - videos/motivation/closing_{archetype}_day{XX}.mp4
        - videos/motivation/main_motivation_{archetype}_day{XX}.mp4
        - videos/motivation/trainer_speech_{archetype}_day{XX}.mp4
        - videos/motivation/warmup_motivation_{archetype}_day{XX}.mp4
        """
        
        if not path.startswith('videos/motivation/'):
            return None
            
        filename = path.split('/')[-1].rsplit('.', 1)[0]  # Remove extension
        
        # Parse the actual structure: {type}_{archetype}_day{XX}
        parts = filename.split('_')
        
        if len(parts) >= 3:
            # Extract day number from last part (day01 -> 01)
            day_part = parts[-1]
            if day_part.startswith('day'):
                day_number = day_part.replace('day', '')
                
                # Get archetype (second to last part)
                archetype = self._normalize_archetype(parts[-2])
                
                # Get video type (everything before archetype)
                video_type = '_'.join(parts[:-2])
                
                # Map video types to categories
                if video_type == 'intro':
                    return ('daily_intro', archetype, day_number, parts[-2])
                elif video_type == 'closing':
                    return ('daily_closing', archetype, day_number, parts[-2])
                elif video_type == 'main_motivation':
                    return ('daily_main_motivation', archetype, day_number, parts[-2])
                elif video_type == 'trainer_speech':
                    return ('daily_trainer_speech', archetype, day_number, parts[-2])
                elif video_type == 'warmup_motivation':
                    return ('daily_warmup_motivation', archetype, day_number, parts[-2])
                else:
                    return ('daily_other', archetype, f"{video_type}_{day_number}", parts[-2])
        
        if self.verbose:
            self.stdout.write(f"  ⚠️  Unmatched motivational: {path}")
        
        return None

    def _parse_speech_path(self, path: str) -> Tuple[str, str, str, str] or None:
        """
        Parse speech video file path into components
        
        Expected formats:
        - videos/speech/{archetype}_speech_{type}.mp4
        - videos/speech/{archetype}_trainer_intro.mp4
        """
        
        if not path.startswith('videos/speech/'):
            return None
            
        filename = path.split('/')[-1].rsplit('.', 1)[0]
        
        # Speech videos: {archetype}_speech_{type}
        if '_speech_' in filename:
            parts = filename.split('_speech_')
            if len(parts) == 2:
                archetype = self._normalize_archetype(parts[0])
                speech_type = parts[1]
                return ('speech', archetype, speech_type, parts[0])
        
        # Trainer intro: {archetype}_trainer_intro
        elif filename.endswith('_trainer_intro'):
            archetype = self._normalize_archetype(filename.replace('_trainer_intro', ''))
            return ('speech', archetype, 'trainer_intro', archetype)
        
        if self.verbose:
            self.stdout.write(f"  ⚠️  Unmatched speech: {path}")
        
        return None

    def _normalize_archetype(self, archetype_name: str) -> str:
        """Normalize archetype name to standard format"""
        # Map R2 folder names to our archetype system
        archetype_map = {
            'best_mate': 'peer',
            'pro_coach': 'professional', 
            'wise_mentor': 'mentor',
            'bro': 'peer',
            'sergeant': 'professional',
            'intellectual': 'mentor',
            'peer': 'peer',
            'professional': 'professional',
            'mentor': 'mentor'
        }
        return archetype_map.get(archetype_name.lower(), archetype_name.lower())

    def _analyze_motivational_structure(self, motivational_structure: Dict):
        """Analyze and report motivational video structure"""
        self.stdout.write('\n📊 MOTIVATIONAL VIDEO STRUCTURE ANALYSIS')
        self.stdout.write('=' * 60)
        
        total_videos = 0
        archetype_counts = defaultdict(int)
        
        for video_type, archetypes in motivational_structure.items():
            type_videos = sum(len(videos) for videos in archetypes.values())
            total_videos += type_videos
            
            self.stdout.write(f'\n{video_type.upper()}:')
            self.stdout.write(f'  Total videos: {type_videos}')
            
            for archetype, videos in archetypes.items():
                archetype_counts[archetype] += len(videos)
                self.stdout.write(f'  {archetype}: {len(videos)} videos')
                
                if self.verbose and videos:
                    for video in videos[:3]:  # Show first 3 examples
                        self.stdout.write(f'    - {video["identifier"]} ({video["size"]} bytes)')
                    if len(videos) > 3:
                        self.stdout.write(f'    ... and {len(videos) - 3} more')
        
        self.stdout.write(f'\n📈 TOTALS:')
        self.stdout.write(f'  Total motivational videos: {total_videos}')
        
        for archetype, count in archetype_counts.items():
            self.stdout.write(f'  {archetype}: {count} videos')
        
        # Calculate expected video counts for 3-week program
        expected_counts = self._calculate_expected_video_counts()
        self.stdout.write(f'\n📋 EXPECTED COUNTS FOR 3-WEEK PROGRAM:')
        for video_type, count in expected_counts.items():
            self.stdout.write(f'  {video_type}: {count} videos per archetype')

    def _calculate_expected_video_counts(self) -> Dict[str, int]:
        """Calculate expected video counts for 3-week program"""
        return {
            'daily_intro': 21,  # 21 days × intro videos
            'daily_closing': 21,  # 21 days × closing videos
            'daily_main_motivation': 21,  # 21 days × main motivation
            'daily_trainer_speech': 21,  # 21 days × trainer speech
            'daily_warmup_motivation': 21,  # 21 days × warmup motivation
            'weekly': 3,  # 3 weeks × weekly lesson (if exists)
            'completion': 1,  # Final completion video (if exists)
        }

    def _index_motivational_videos(self, motivational_structure: Dict):
        """Index motivational videos in database"""
        self.stdout.write('\n🏗️  INDEXING MOTIVATIONAL VIDEOS')
        self.stdout.write('=' * 60)
        
        created_clips = 0
        updated_lessons = 0
        
        for video_type, archetypes in motivational_structure.items():
            for archetype, videos in archetypes.items():
                
                if video_type == 'weekly':
                    # Handle weekly lesson videos
                    for video in videos:
                        week_num = self._extract_week_number(video['identifier'])
                        if week_num:
                            # Update or create WeeklyLesson record
                            lesson, created = WeeklyLesson.objects.get_or_create(
                                week=week_num,
                                archetype=self._convert_to_archetype_code(archetype),
                                defaults={
                                    'title': f'Урок недели {week_num}',
                                    'script': f'Мотивационный урок недели {week_num} для архетипа {archetype}',
                                    'duration_sec': 180
                                }
                            )
                            if created:
                                updated_lessons += 1
                
                elif video_type == 'completion':
                    # Handle final completion videos
                    for video in videos:
                        final_video, created = FinalVideo.objects.get_or_create(
                            arch=self._convert_to_archetype_code(archetype),
                            defaults={
                                'script': f'Поздравительное видео для архетипа {archetype}'
                            }
                        )
                        if created:
                            updated_lessons += 1
                
                else:
                    # Handle other motivational videos as VideoClip records
                    for video in videos:
                        # Create VideoClip record for motivational content
                        clip, created = VideoClip.objects.get_or_create(
                            exercise=None,  # Motivational videos are not exercise-specific
                            r2_kind=self._map_to_video_kind(video_type, video['identifier']),
                            archetype=archetype,
                            model_name=video.get('trainer_name', 'default'),
                            defaults={
                                'r2_file': video['key'],
                                'duration_seconds': 60,  # Default duration
                                'provider': 'r2',
                                'is_active': True,
                                'script_text': f'{video_type.title()} motivational content'
                            }
                        )
                        
                        if created:
                            created_clips += 1
        
        self.stdout.write(f'✅ Created {created_clips} new motivational video clips')
        self.stdout.write(f'✅ Updated {updated_lessons} weekly lessons and final videos')

    def _extract_week_number(self, identifier: str) -> int or None:
        """Extract week number from identifier like 'week1', 'week2'"""
        if identifier.startswith('week'):
            try:
                return int(identifier.replace('week', ''))
            except ValueError:
                pass
        return None

    def _convert_to_archetype_code(self, archetype: str) -> str:
        """Convert archetype to database code format"""
        code_map = {
            'mentor': '111',
            'professional': '222',
            'peer': '333'
        }
        return code_map.get(archetype, '111')

    def _map_to_video_kind(self, video_type: str, identifier: str) -> str:
        """Map video type and identifier to VideoKind enum"""
        kind_mapping = {
            'daily_intro': VideoKind.INTRO,
            'daily_closing': VideoKind.CLOSING,
            'daily_main_motivation': VideoKind.WEEKLY,  # General motivation
            'daily_trainer_speech': VideoKind.EXPLAIN,
            'daily_warmup_motivation': VideoKind.CONTEXTUAL_INTRO,
            'weekly': VideoKind.WEEKLY,
            'completion': VideoKind.CONTEXTUAL_OUTRO,
            'speech': VideoKind.EXPLAIN
        }
        return kind_mapping.get(video_type, VideoKind.WEEKLY)