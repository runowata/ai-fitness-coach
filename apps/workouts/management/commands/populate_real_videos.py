"""
Management command to populate VideoClip records based on real video structure on Render
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from apps.workouts.models import VideoClip, Exercise


class Command(BaseCommand):
    help = 'Populate VideoClip records based on real video structure on Render'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating records',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write('Populating VideoClip records for real video structure...')
        
        # Clear existing VideoClip records
        if not dry_run:
            VideoClip.objects.all().delete()
            self.stdout.write('Cleared existing VideoClip records')
        
        created_count = 0
        
        with transaction.atomic():
            # Get all exercises
            exercises = list(Exercise.objects.all())
            
            # Create exercise video records
            for i, exercise in enumerate(exercises, 1):
                ex_code = f"EX{i:03d}"  # EX001, EX002, etc.
                created = self.create_exercise_videos(exercise, ex_code, dry_run)
                created_count += created
            
            # Create trainer videos
            created = self.create_trainer_videos(dry_run)
            created_count += created
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'DRY RUN: Would create {created_count} VideoClip records')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} VideoClip records!')
            )
            
            # Show summary
            self.stdout.write('\n=== SUMMARY ===')
            for video_type in ['technique', 'mistake', 'instruction', 'reminder', 'final', 'weekly']:
                count = VideoClip.objects.filter(type=video_type).count()
                self.stdout.write(f'{video_type}: {count} videos')
    
    def create_exercise_videos(self, exercise, ex_code, dry_run):
        """Create all video types for an exercise based on real structure"""
        created_count = 0
        base_url = '/media/videos/exercises/'
        
        # Technique videos (3 variants, no archetype)
        for mod_num in range(1, 4):
            url = f"{base_url}{ex_code}/technique_mod{mod_num}.mp4"
            
            if not dry_run:
                VideoClip.objects.create(
                    exercise=exercise,
                    type='technique',
                    archetype='bro',  # Default for technique
                    model_name=f'mod{mod_num}',
                    url=url,
                    duration_seconds=45,
                    is_active=True
                )
            
            created_count += 1
            self.stdout.write(f'  Created: {url}')
        
        # Mistake videos (3 variants, no archetype)
        for mod_num in range(1, 4):
            url = f"{base_url}{ex_code}/mistake_mod{mod_num}.mp4"
            
            if not dry_run:
                VideoClip.objects.create(
                    exercise=exercise,
                    type='mistake',
                    archetype='bro',  # Default for mistakes
                    model_name=f'mod{mod_num}',
                    url=url,
                    duration_seconds=30,
                    is_active=True
                )
            
            created_count += 1
            self.stdout.write(f'  Created: {url}')
        
        # Instruction videos (3 archetypes × 3 models)
        archetypes = ['bro', 'sergeant', 'intellectual']
        for archetype in archetypes:
            for mod_num in range(1, 4):
                url = f"{base_url}{ex_code}/instruction_{archetype}_mod{mod_num}.mp4"
                
                if not dry_run:
                    VideoClip.objects.create(
                        exercise=exercise,
                        type='instruction',
                        archetype=archetype,
                        model_name=f'mod{mod_num}',
                        url=url,
                        duration_seconds=60,
                        is_active=True
                    )
                
                created_count += 1
                self.stdout.write(f'  Created: {url}')
        
        # Reminder videos (3 archetypes × 3 reminders)
        for archetype in archetypes:
            for reminder_num in range(1, 4):
                url = f"{base_url}{ex_code}/reminder_{archetype}_{reminder_num}.mp4"
                
                if not dry_run:
                    VideoClip.objects.create(
                        exercise=exercise,
                        type='reminder',
                        archetype=archetype,
                        model_name='mod1',
                        url=url,
                        duration_seconds=20,
                        reminder_text=f'{archetype}_reminder_{reminder_num}',
                        is_active=True
                    )
                
                created_count += 1
                self.stdout.write(f'  Created: {url}')
        
        return created_count
    
    def create_trainer_videos(self, dry_run):
        """Create trainer videos (final, weekly, cycle completion)"""
        created_count = 0
        base_url = '/media/videos/trainers/'
        
        archetypes = ['bro', 'sergeant', 'intellectual']
        
        # Final videos (daily workout completion) - 3 per archetype
        for archetype in archetypes:
            for mod_num in range(1, 4):
                url = f"{base_url}{archetype}_final_mod{mod_num}.mp4"
                
                if not dry_run:
                    VideoClip.objects.create(
                        exercise=None,
                        type='final',
                        archetype=archetype,
                        model_name=f'mod{mod_num}',
                        url=url,
                        duration_seconds=30,
                        is_active=True
                    )
                
                created_count += 1
                self.stdout.write(f'  Created: {url}')
        
        # Weekly motivation videos - 6 weeks per archetype
        for archetype in archetypes:
            for week in range(1, 7):
                url = f"{base_url}{archetype}_weekly_week{week}.mp4"
                
                if not dry_run:
                    VideoClip.objects.create(
                        exercise=None,
                        type='weekly',
                        archetype=archetype,
                        model_name=f'week{week}',
                        url=url,
                        duration_seconds=60,
                        reminder_text=f'week{week}_motivation',
                        is_active=True
                    )
                
                created_count += 1
                self.stdout.write(f'  Created: {url}')
        
        # Cycle completion videos - 3 per archetype
        for archetype in archetypes:
            for mod_num in range(1, 4):
                url = f"{base_url}{archetype}_cycle_complete_mod{mod_num}.mp4"
                
                if not dry_run:
                    VideoClip.objects.create(
                        exercise=None,
                        type='final',
                        archetype=archetype,
                        model_name=f'mod{mod_num}',
                        url=url,
                        duration_seconds=90,
                        reminder_text=f'cycle_complete_{archetype}_celebration',
                        is_active=True
                    )
                
                created_count += 1
                self.stdout.write(f'  Created: {url}')
        
        return created_count