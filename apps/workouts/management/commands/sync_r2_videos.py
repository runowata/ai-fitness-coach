#!/usr/bin/env python3
"""
Management command to sync existing R2 videos with database
Discovers video files in Cloudflare R2 and creates VideoClip records
"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.workouts.constants import Archetype, VideoKind
from apps.workouts.models import CSVExercise, VideoClip, VideoProvider

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync existing videos from Cloudflare R2 with database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of videos to process (for testing)'
        )
        parser.add_argument(
            '--prefix',
            type=str,
            default='videos/',
            help='R2 prefix to scan for videos (default: videos/)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Update existing VideoClip records if they exist'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.limit = options['limit']
        self.prefix = options['prefix']
        self.force = options['force']
        self.verbose = options['verbose']

        if self.verbose:
            logger.setLevel(logging.DEBUG)

        self.stdout.write("🔍 SYNC R2 VIDEOS WITH DATABASE")
        self.stdout.write("=" * 50)
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        # Check R2 configuration
        if not self._check_r2_config():
            raise CommandError("R2 configuration is incomplete")
        
        # Get S3 client
        try:
            s3_client = self._get_s3_client()
        except Exception as e:
            raise CommandError(f"Failed to create S3 client: {e}")
        
        # Discover videos in R2
        self.stdout.write(f"📂 Scanning R2 bucket for videos with prefix '{self.prefix}'...")
        video_files = self._discover_r2_videos(s3_client)
        
        if not video_files:
            self.stdout.write(self.style.WARNING("No video files found in R2"))
            return
        
        self.stdout.write(f"Found {len(video_files)} video files in R2")
        
        if self.limit:
            video_files = video_files[:self.limit]
            self.stdout.write(f"Limited to {len(video_files)} files for processing")
        
        # Process discovered videos
        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for i, (s3_key, size, modified) in enumerate(video_files, 1):
            self.stdout.write(f"Processing {i}/{len(video_files)}: {s3_key}")
            
            try:
                result = self._process_video_file(s3_key, size, modified)
                
                if result == 'created':
                    created_count += 1
                elif result == 'updated':
                    updated_count += 1
                elif result == 'skipped':
                    skipped_count += 1
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"Error processing {s3_key}: {e}")
                )
                if self.verbose:
                    import traceback
                    self.stdout.write(traceback.format_exc())
        
        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("📊 SYNC SUMMARY")
        self.stdout.write(f"   Created: {created_count}")
        self.stdout.write(f"   Updated: {updated_count}")
        self.stdout.write(f"   Skipped: {skipped_count}")
        self.stdout.write(f"   Errors:  {error_count}")
        self.stdout.write(f"   Total:   {len(video_files)}")

    def _check_r2_config(self) -> bool:
        """Check if R2 configuration is available"""
        
        # Get values from env and settings
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY') 
        bucket_name = os.getenv('R2_BUCKET') or os.getenv('AWS_STORAGE_BUCKET_NAME') or getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
        endpoint_url = os.getenv('R2_ENDPOINT') or os.getenv('AWS_S3_ENDPOINT_URL') or getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
        
        required_settings = [
            ('AWS_ACCESS_KEY_ID', access_key),
            ('AWS_SECRET_ACCESS_KEY', secret_key),
            ('BUCKET_NAME', bucket_name),
            ('ENDPOINT_URL', endpoint_url),
        ]
        
        missing = []
        for name, value in required_settings:
            if not value:
                missing.append(name)
        
        if missing:
            for name in missing:
                self.stdout.write(self.style.ERROR(f"Missing R2 setting: {name}"))
            return False
        
        return True

    def _get_s3_client(self):
        """Create S3 client for R2"""
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

    def _discover_r2_videos(self, s3_client) -> List[Tuple[str, int, str]]:
        """Discover video files in R2 bucket"""
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}
        video_files = []
        
        try:
            bucket_name = os.getenv('R2_BUCKET') or os.getenv('AWS_STORAGE_BUCKET_NAME') or getattr(settings, 'AWS_STORAGE_BUCKET_NAME')
            paginator = s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=bucket_name, Prefix=self.prefix):
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    key = obj['Key']
                    
                    # Check if it's a video file
                    if any(key.lower().endswith(ext) for ext in video_extensions):
                        video_files.append((
                            key,
                            obj['Size'],
                            obj['LastModified'].isoformat()
                        ))
                        
                        if self.verbose:
                            self.stdout.write(f"  Found: {key} ({obj['Size']} bytes)")
            
        except ClientError as e:
            raise CommandError(f"Failed to list R2 objects: {e}")
        
        return video_files

    def _process_video_file(self, s3_key: str, size: int, modified: str) -> str:
        """Process a single video file from R2"""
        
        # Parse video file metadata from path
        video_metadata = self._parse_video_path(s3_key)
        
        if not video_metadata:
            if self.verbose:
                self.stdout.write(f"  Skipped: Could not parse metadata from {s3_key}")
            return 'skipped'
        
        # Check if VideoClip already exists
        existing_clip = self._find_existing_clip(video_metadata, s3_key)
        
        if existing_clip and not self.force:
            if self.verbose:
                self.stdout.write(f"  Skipped: VideoClip already exists for {s3_key}")
            return 'skipped'
        
        # Create or update VideoClip
        if self.dry_run:
            action = 'UPDATE' if existing_clip else 'CREATE'
            self.stdout.write(f"  [DRY RUN] Would {action}: {s3_key} -> {video_metadata}")
            return 'created' if not existing_clip else 'updated'
        
        with transaction.atomic():
            if existing_clip:
                # Update existing clip
                self._update_video_clip(existing_clip, video_metadata, s3_key, size)
                self.stdout.write(self.style.SUCCESS(f"  Updated: {s3_key}"))
                return 'updated'
            else:
                # Create new clip
                clip = self._create_video_clip(video_metadata, s3_key, size)
                self.stdout.write(self.style.SUCCESS(f"  Created: {clip.id} for {s3_key}"))
                return 'created'

    def _parse_video_path(self, s3_key: str) -> Optional[Dict]:
        """
        Parse video file path to extract metadata
        
        Expected formats based on reference materials:
        - videos/exercises/{slug}_technique_{model}.mp4
        - videos/exercises/{slug}_mistake_{model}.mp4  
        - videos/instructions/{slug}_instruction_{archetype}_{model}.mp4
        - videos/reminders/{slug}_reminder_{archetype}_{number}.mp4
        - videos/motivation/weekly_{archetype}_week{number}.mp4
        - videos/intro/{archetype}_intro_{variation}.mp4
        - videos/outro/{archetype}_outro_{variation}.mp4
        """
        
        patterns = [
            # Exercise technique/mistake videos
            (r'videos/exercises/([^_]+)_(technique|mistake)_([^/]+)\.mp4$', 'exercise_basic'),
            
            # Instruction videos  
            (r'videos/instructions/([^_]+)_instruction_(mentor|professional|peer)_([^/]+)\.mp4$', 'exercise_instruction'),
            
            # Reminder videos
            (r'videos/reminders/([^_]+)_reminder_(mentor|professional|peer)_(\d+)\.mp4$', 'exercise_reminder'),
            
            # Weekly motivation
            (r'videos/motivation/weekly_(mentor|professional|peer)_week(\d+)\.mp4$', 'weekly_motivation'),
            
            # Contextual intro/outro
            (r'videos/(intro|outro)/(mentor|professional|peer)_(intro|outro)_(\d+)\.mp4$', 'contextual'),
            
            # Mid-workout motivation  
            (r'videos/mid_workout/(mentor|professional|peer)_mid_(\d+)\.mp4$', 'mid_workout'),
        ]
        
        for pattern, video_type in patterns:
            match = re.match(pattern, s3_key)
            if match:
                return self._extract_metadata_from_match(match, video_type, s3_key)
        
        # Try generic pattern
        if 'videos/' in s3_key:
            return self._parse_generic_video_path(s3_key)
        
        return None

    def _extract_metadata_from_match(self, match, video_type: str, s3_key: str) -> Dict:
        """Extract metadata from regex match based on video type"""
        
        if video_type == 'exercise_basic':
            exercise_slug, kind, model = match.groups()
            return {
                'exercise_slug': exercise_slug,
                'r2_kind': kind,
                'r2_archetype': 'mentor',  # Default for basic exercise videos
                'model_name': model,
                'video_type': 'exercise',
                's3_key': s3_key
            }
        
        elif video_type == 'exercise_instruction':
            exercise_slug, archetype, model = match.groups()
            return {
                'exercise_slug': exercise_slug,
                'r2_kind': VideoKind.INSTRUCTION,
                'r2_archetype': archetype,
                'model_name': model,
                'video_type': 'exercise',
                's3_key': s3_key
            }
        
        elif video_type == 'exercise_reminder':
            exercise_slug, archetype, number = match.groups()
            return {
                'exercise_slug': exercise_slug,
                'r2_kind': VideoKind.REMINDER,
                'r2_archetype': archetype,
                'model_name': f'reminder_{number}',
                'reminder_text': f'Reminder {number}',
                'video_type': 'exercise',
                's3_key': s3_key
            }
        
        elif video_type == 'weekly_motivation':
            archetype, week_number = match.groups()
            return {
                'exercise_slug': None,
                'r2_kind': VideoKind.WEEKLY,
                'r2_archetype': archetype,
                'model_name': f'week_{week_number}',
                'week_context': int(week_number),
                'video_type': 'global',
                's3_key': s3_key
            }
        
        elif video_type == 'contextual':
            category, archetype, kind, variation = match.groups()
            r2_kind = VideoKind.CONTEXTUAL_INTRO if kind == 'intro' else VideoKind.CONTEXTUAL_OUTRO
            return {
                'exercise_slug': None,
                'r2_kind': r2_kind,
                'r2_archetype': archetype,
                'model_name': f'{kind}_{variation}',
                'variation_number': int(variation),
                'position_in_workout': 'intro' if kind == 'intro' else 'outro',
                'video_type': 'global',
                's3_key': s3_key
            }
        
        elif video_type == 'mid_workout':
            archetype, variation = match.groups()
            return {
                'exercise_slug': None,
                'r2_kind': VideoKind.MID_WORKOUT,
                'r2_archetype': archetype,
                'model_name': f'mid_{variation}',
                'variation_number': int(variation),
                'position_in_workout': 'mid',
                'video_type': 'global',
                's3_key': s3_key
            }
        
        return {}

    def _parse_generic_video_path(self, s3_key: str) -> Optional[Dict]:
        """Parse generic video path as fallback"""
        
        # Extract basic info from path
        parts = s3_key.split('/')
        if len(parts) < 2:
            return None
        
        filename = parts[-1]
        category = parts[-2] if len(parts) > 1 else 'unknown'
        
        # Try to determine archetype from filename
        archetype = 'mentor'  # Default
        for arch in ['mentor', 'professional', 'peer']:
            if arch in filename.lower():
                archetype = arch
                break
        
        # Try to determine video kind
        r2_kind = VideoKind.INSTRUCTION  # Default
        kind_mapping = {
            'technique': VideoKind.TECHNIQUE,
            'mistake': VideoKind.MISTAKE,
            'instruction': VideoKind.INSTRUCTION,
            'intro': VideoKind.INTRO,
            'outro': VideoKind.CLOSING,
            'weekly': VideoKind.WEEKLY,
            'mid': VideoKind.MID_WORKOUT,
        }
        
        for keyword, kind in kind_mapping.items():
            if keyword in filename.lower():
                r2_kind = kind
                break
        
        return {
            'exercise_slug': None,
            'r2_kind': r2_kind,
            'r2_archetype': archetype,
            'model_name': filename.split('.')[0],  # Remove extension
            'video_type': 'global',
            's3_key': s3_key
        }

    def _find_existing_clip(self, metadata: Dict, s3_key: str) -> Optional[VideoClip]:
        """Find existing VideoClip record"""
        
        # Build query filters
        filters = {
            'r2_kind': metadata['r2_kind'],
            'r2_archetype': metadata['r2_archetype'],
            'model_name': metadata['model_name'],
        }
        
        # Add exercise if specified
        if metadata.get('exercise_slug'):
            try:
                exercise = CSVExercise.objects.get(id=metadata['exercise_slug'])
                filters['exercise'] = exercise
            except CSVExercise.DoesNotExist:
                if self.verbose:
                    self.stdout.write(f"  Warning: Exercise {metadata['exercise_slug']} not found")
                return None
        else:
            filters['exercise__isnull'] = True
        
        # Add optional fields
        if 'reminder_text' in metadata:
            filters['reminder_text'] = metadata['reminder_text']
        
        try:
            return VideoClip.objects.get(**filters)
        except VideoClip.DoesNotExist:
            return None
        except VideoClip.MultipleObjectsReturned:
            # Return first match if multiple found
            return VideoClip.objects.filter(**filters).first()

    def _create_video_clip(self, metadata: Dict, s3_key: str, size: int) -> VideoClip:
        """Create new VideoClip record"""
        
        clip_data = {
            'r2_kind': metadata['r2_kind'],
            'r2_archetype': metadata['r2_archetype'],
            'model_name': metadata['model_name'],
            'provider': VideoProvider.R2,
            'duration_seconds': 60,  # Default, can be updated later
            'is_active': True,
        }
        
        # Add exercise if specified
        if metadata.get('exercise_slug'):
            try:
                exercise = CSVExercise.objects.get(id=metadata['exercise_slug'])
                clip_data['exercise'] = exercise
            except CSVExercise.DoesNotExist:
                if self.verbose:
                    self.stdout.write(f"  Warning: Exercise {metadata['exercise_slug']} not found")
        
        # Add contextual fields
        for field in ['mood_type', 'content_theme', 'position_in_workout', 'week_context', 'variation_number', 'reminder_text']:
            if field in metadata:
                clip_data[field] = metadata[field]
        
        # Create the clip
        clip = VideoClip.objects.create(**clip_data)
        
        # Set the r2_file field (this is tricky - we need to create a File instance)
        # For now, we'll just store the S3 key in a custom field or leave it empty
        # The video_storage.py will handle URL generation based on the S3 key
        
        return clip

    def _update_video_clip(self, clip: VideoClip, metadata: Dict, s3_key: str, size: int):
        """Update existing VideoClip record"""
        
        # Update contextual fields
        updated_fields = []
        for field in ['mood_type', 'content_theme', 'position_in_workout', 'week_context', 'variation_number']:
            if field in metadata and hasattr(clip, field):
                old_value = getattr(clip, field)
                new_value = metadata[field]
                if old_value != new_value:
                    setattr(clip, field, new_value)
                    updated_fields.append(field)
        
        if updated_fields:
            clip.save(update_fields=updated_fields)
            if self.verbose:
                self.stdout.write(f"    Updated fields: {updated_fields}")