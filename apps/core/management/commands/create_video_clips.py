"""
Management command to create VideoClip records for existing media files
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.workouts.models import VideoClip, Exercise
from apps.onboarding.models import MotivationalCard


class Command(BaseCommand):
    help = 'Create VideoClip records for video files in media storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating records',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write('Creating VideoClip records for media files...')
        
        created_count = 0
        
        with transaction.atomic():
            # Create exercise video clips
            created_count += self.create_exercise_video_clips(dry_run)
            
            # Create trainer video clips
            created_count += self.create_trainer_video_clips(dry_run)
            
            # Create motivational video clips
            created_count += self.create_motivational_video_clips(dry_run)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would create {created_count} VideoClip records'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created {created_count} VideoClip records'
                )
            )
            
            # Show final statistics
            total_clips = VideoClip.objects.count()
            self.stdout.write(f'Total VideoClip records: {total_clips}')

    def create_exercise_video_clips(self, dry_run):
        """Create VideoClip records for exercise videos"""
        created_count = 0
        
        # Expected exercise video structure in media/videos/exercises/
        exercise_videos = [
            # Push-ups videos
            {'exercise_slug': 'push-ups', 'type': 'technique', 'archetype': None, 'model': 'mod1', 'file': 'videos/exercises/push_ups_technique_mod1.mp4'},
            {'exercise_slug': 'push-ups', 'type': 'instruction', 'archetype': 'bro', 'model': 'mod1', 'file': 'videos/exercises/push_ups_instruction_bro_mod1.mp4'},
            {'exercise_slug': 'push-ups', 'type': 'instruction', 'archetype': 'sergeant', 'model': 'mod1', 'file': 'videos/exercises/push_ups_instruction_sergeant_mod1.mp4'},
            {'exercise_slug': 'push-ups', 'type': 'instruction', 'archetype': 'intellectual', 'model': 'mod1', 'file': 'videos/exercises/push_ups_instruction_intellectual_mod1.mp4'},
            {'exercise_slug': 'push-ups', 'type': 'reminder', 'archetype': 'bro', 'model': None, 'file': 'videos/exercises/push_ups_reminder_bro_1.mp4'},
            {'exercise_slug': 'push-ups', 'type': 'reminder', 'archetype': 'sergeant', 'model': None, 'file': 'videos/exercises/push_ups_reminder_sergeant_1.mp4'},
            {'exercise_slug': 'push-ups', 'type': 'reminder', 'archetype': 'intellectual', 'model': None, 'file': 'videos/exercises/push_ups_reminder_intellectual_1.mp4'},
            {'exercise_slug': 'push-ups', 'type': 'mistake', 'archetype': None, 'model': 'mod1', 'file': 'videos/exercises/push_ups_mistake_mod1.mp4'},
            
            # Squats videos
            {'exercise_slug': 'squats', 'type': 'technique', 'archetype': None, 'model': 'mod1', 'file': 'videos/exercises/squats_technique_mod1.mp4'},
            {'exercise_slug': 'squats', 'type': 'instruction', 'archetype': 'bro', 'model': 'mod1', 'file': 'videos/exercises/squats_instruction_bro_mod1.mp4'},
            {'exercise_slug': 'squats', 'type': 'instruction', 'archetype': 'sergeant', 'model': 'mod1', 'file': 'videos/exercises/squats_instruction_sergeant_mod1.mp4'},
            {'exercise_slug': 'squats', 'type': 'instruction', 'archetype': 'intellectual', 'model': 'mod1', 'file': 'videos/exercises/squats_instruction_intellectual_mod1.mp4'},
            {'exercise_slug': 'squats', 'type': 'reminder', 'archetype': 'bro', 'model': None, 'file': 'videos/exercises/squats_reminder_bro_1.mp4'},
            {'exercise_slug': 'squats', 'type': 'reminder', 'archetype': 'sergeant', 'model': None, 'file': 'videos/exercises/squats_reminder_sergeant_1.mp4'},
            {'exercise_slug': 'squats', 'type': 'reminder', 'archetype': 'intellectual', 'model': None, 'file': 'videos/exercises/squats_reminder_intellectual_1.mp4'},
            {'exercise_slug': 'squats', 'type': 'mistake', 'archetype': None, 'model': 'mod1', 'file': 'videos/exercises/squats_mistake_mod1.mp4'},
            
            # Plank videos
            {'exercise_slug': 'plank', 'type': 'technique', 'archetype': None, 'model': 'mod1', 'file': 'videos/exercises/plank_technique_mod1.mp4'},
            {'exercise_slug': 'plank', 'type': 'instruction', 'archetype': 'bro', 'model': 'mod1', 'file': 'videos/exercises/plank_instruction_bro_mod1.mp4'},
            {'exercise_slug': 'plank', 'type': 'instruction', 'archetype': 'sergeant', 'model': 'mod1', 'file': 'videos/exercises/plank_instruction_sergeant_mod1.mp4'},
            {'exercise_slug': 'plank', 'type': 'instruction', 'archetype': 'intellectual', 'model': 'mod1', 'file': 'videos/exercises/plank_instruction_intellectual_mod1.mp4'},
            {'exercise_slug': 'plank', 'type': 'reminder', 'archetype': 'bro', 'model': None, 'file': 'videos/exercises/plank_reminder_bro_1.mp4'},
            {'exercise_slug': 'plank', 'type': 'reminder', 'archetype': 'sergeant', 'model': None, 'file': 'videos/exercises/plank_reminder_sergeant_1.mp4'},
            {'exercise_slug': 'plank', 'type': 'reminder', 'archetype': 'intellectual', 'model': None, 'file': 'videos/exercises/plank_reminder_intellectual_1.mp4'},
            {'exercise_slug': 'plank', 'type': 'mistake', 'archetype': None, 'model': 'mod1', 'file': 'videos/exercises/plank_mistake_mod1.mp4'},
        ]
        
        for video_data in exercise_videos:
            try:
                # Get exercise
                exercise = Exercise.objects.get(slug=video_data['exercise_slug'])
                
                if not dry_run:
                    video_clip, created = VideoClip.objects.get_or_create(
                        exercise=exercise,
                        type=video_data['type'],
                        archetype=video_data['archetype'],
                        model_name=video_data['model'],
                        defaults={
                            'url': f'/media/{video_data["file"]}',
                            'duration_seconds': 45,  # Default duration
                            'is_active': True,
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f'  ✓ Created exercise video: {video_data["file"]}')
                    else:
                        self.stdout.write(f'  → Already exists: {video_data["file"]}')
                else:
                    self.stdout.write(f'  → Would create: {video_data["file"]}')
                    created_count += 1
                    
            except Exercise.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Exercise not found: {video_data["exercise_slug"]}')
                )
        
        return created_count

    def create_trainer_video_clips(self, dry_run):
        """Create VideoClip records for trainer videos"""
        created_count = 0
        
        # Expected trainer video structure in media/videos/trainers/
        trainer_videos = [
            # Intro videos
            {'type': 'instruction', 'archetype': 'bro', 'file': 'videos/trainers/bro_intro_1.mp4'},
            {'type': 'instruction', 'archetype': 'sergeant', 'file': 'videos/trainers/sergeant_intro_1.mp4'},
            {'type': 'instruction', 'archetype': 'intellectual', 'file': 'videos/trainers/intellectual_intro_1.mp4'},
            
            # Weekly motivation videos
            {'type': 'weekly', 'archetype': 'bro', 'file': 'videos/trainers/bro_weekly_1.mp4'},
            {'type': 'weekly', 'archetype': 'sergeant', 'file': 'videos/trainers/sergeant_weekly_1.mp4'},
            {'type': 'weekly', 'archetype': 'intellectual', 'file': 'videos/trainers/intellectual_weekly_1.mp4'},
            
            # Final videos
            {'type': 'final', 'archetype': 'bro', 'file': 'videos/trainers/bro_final_1.mp4'},
            {'type': 'final', 'archetype': 'sergeant', 'file': 'videos/trainers/sergeant_final_1.mp4'},
            {'type': 'final', 'archetype': 'intellectual', 'file': 'videos/trainers/intellectual_final_1.mp4'},
        ]
        
        for video_data in trainer_videos:
            if not dry_run:
                video_clip, created = VideoClip.objects.get_or_create(
                    exercise=None,  # Trainer videos not linked to specific exercise
                    type=video_data['type'],
                    archetype=video_data['archetype'],
                    url=f'/media/{video_data["file"]}',
                    defaults={
                        'duration_seconds': 60,  # Default duration
                        'is_active': True,
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'  ✓ Created trainer video: {video_data["file"]}')
                else:
                    self.stdout.write(f'  → Already exists: {video_data["file"]}')
            else:
                self.stdout.write(f'  → Would create: {video_data["file"]}')
                created_count += 1
        
        return created_count

    def create_motivational_video_clips(self, dry_run):
        """Create VideoClip records for motivational videos"""
        created_count = 0
        
        # Expected motivational video structure in media/videos/motivation/
        motivational_videos = [
            {'type': 'motivation', 'archetype': 'bro', 'file': 'videos/motivation/bro_motivation_1.mp4'},
            {'type': 'motivation', 'archetype': 'sergeant', 'file': 'videos/motivation/sergeant_motivation_1.mp4'},
            {'type': 'motivation', 'archetype': 'intellectual', 'file': 'videos/motivation/intellectual_motivation_1.mp4'},
        ]
        
        for video_data in motivational_videos:
            if not dry_run:
                video_clip, created = VideoClip.objects.get_or_create(
                    exercise=None,
                    type=video_data['type'],
                    archetype=video_data['archetype'],
                    url=f'/media/{video_data["file"]}',
                    defaults={
                        'duration_seconds': 30,  # Default duration
                        'is_active': True,
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'  ✓ Created motivational video: {video_data["file"]}')
                else:
                    self.stdout.write(f'  → Already exists: {video_data["file"]}')
            else:
                self.stdout.write(f'  → Would create: {video_data["file"]}')
                created_count += 1
        
        return created_count