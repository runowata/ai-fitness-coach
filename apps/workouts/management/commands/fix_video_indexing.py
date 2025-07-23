import os
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.workouts.models import Exercise, VideoClip

class Command(BaseCommand):
    help = 'Fix video indexing - extract exercise ID from directory name'

    def add_arguments(self, parser):
        parser.add_argument('--media-path', type=str, default='/opt/render/project/src/media/videos',
                          help='Path to media files on Render disk')
        parser.add_argument('--dry-run', action='store_true',
                          help='Show what would be created without saving')
        parser.add_argument('--clear-existing', action='store_true',
                          help='Clear existing data before indexing')

    def handle(self, *args, **options):
        media_path = options['media_path']
        dry_run = options['dry_run']
        clear_existing = options['clear_existing']
        
        self.stdout.write("🚀 FIXING VIDEO INDEXING...")
        self.stdout.write(f"📁 Scanning path: {media_path}")
        
        if not os.path.exists(media_path):
            self.stdout.write(f"❌ Media path not found: {media_path}")
            return
        
        # Find exercise directories (EX001, EX002, etc.)
        exercises_dir = os.path.join(media_path, 'exercises')
        if not os.path.exists(exercises_dir):
            self.stdout.write(f"❌ Exercises directory not found: {exercises_dir}")
            return
        
        exercise_dirs = [d for d in os.listdir(exercises_dir) 
                        if os.path.isdir(os.path.join(exercises_dir, d)) and d.startswith('EX')]
        
        self.stdout.write(f"💪 Found {len(exercise_dirs)} exercise directories")
        
        exercises_data = {}
        videos_data = []
        
        for ex_dir in exercise_dirs:
            exercise_path = os.path.join(exercises_dir, ex_dir)
            
            # Extract exercise ID from directory name (EX003 -> EX003)
            exercise_id = ex_dir
            
            # Find video files in this exercise directory
            video_files = [f for f in os.listdir(exercise_path) if f.endswith('.mp4')]
            
            if not video_files:
                continue
                
            # Create exercise entry
            exercises_data[exercise_id] = {
                'id': exercise_id,
                'name': f'Exercise {exercise_id}',
                'description': f'Exercise {exercise_id} description',
                'difficulty': 'beginner',
                'muscle_groups': ['full_body'],
                'equipment_needed': [],
                'is_active': True
            }
            
            # Process video files
            for video_file in video_files:
                # Parse filename: technique_mod1.mp4, mistake_mod1.mp4
                match = re.match(r'^(.+?)_(.+?)\.mp4$', video_file)
                if match:
                    video_type = match.group(1)  # technique, mistake, etc
                    model_name = match.group(2)  # mod1, mod2, etc
                    
                    # Validate video type
                    valid_types = ['technique', 'mistake', 'instruction', 'reminder', 'weekly', 'final']
                    if video_type not in valid_types:
                        self.stdout.write(f"⚠️  Unknown video type '{video_type}' in {video_file}")
                        continue
                    
                    # Default archetype
                    archetype = 'bro'  # Default since not in filename
                    
                    # Create video entry
                    video_path = os.path.join(exercise_path, video_file)
                    relative_path = os.path.relpath(video_path, '/opt/render/project/src')
                    video_url = f'/{relative_path}'
                    
                    videos_data.append({
                        'exercise_id': exercise_id,
                        'type': video_type,
                        'archetype': archetype,
                        'model_name': model_name,
                        'file_url': video_url,
                        'file_path': video_path
                    })
        
        # Show stats
        self.stdout.write(f"\\n📊 PARSING RESULTS:")
        self.stdout.write(f"   💪 Exercises found: {len(exercises_data)}")
        self.stdout.write(f"   🎬 Videos parsed: {len(videos_data)}")
        
        # Analyze video distribution
        type_stats = {}
        for video in videos_data:
            type_stats[video['type']] = type_stats.get(video['type'], 0) + 1
        
        self.stdout.write(f"\\n📈 VIDEO TYPE DISTRIBUTION:")
        for vtype, count in sorted(type_stats.items()):
            self.stdout.write(f"   {vtype}: {count}")
        
        if dry_run:
            self.stdout.write(f"\\n🔍 DRY RUN - Would create:")
            self.stdout.write(f"   💪 {len(exercises_data)} exercises")
            self.stdout.write(f"   🎬 {len(videos_data)} video clips")
            return
        
        # Save to database
        self.stdout.write(f"\\n💾 SAVING TO DATABASE...")
        
        with transaction.atomic():
            if clear_existing:
                self.stdout.write("🗑️ Clearing existing data...")
                VideoClip.objects.all().delete()
                Exercise.objects.all().delete()
            
            # Create exercises
            created_exercises = 0
            for ex_id, ex_data in exercises_data.items():
                exercise, created = Exercise.objects.get_or_create(
                    id=ex_id,
                    defaults=ex_data
                )
                if created:
                    created_exercises += 1
            
            self.stdout.write(f"✅ Created {created_exercises} exercises")
            
            # Create video clips
            created_videos = 0
            for video_data in videos_data:
                try:
                    exercise = Exercise.objects.get(id=video_data['exercise_id'])
                    
                    video_clip, created = VideoClip.objects.get_or_create(
                        exercise=exercise,
                        type=video_data['type'],
                        archetype=video_data['archetype'],
                        model_name=video_data['model_name'],
                        defaults={
                            'file_url': video_data['file_url'],
                            'is_active': True
                        }
                    )
                    if created:
                        created_videos += 1
                        
                except Exercise.DoesNotExist:
                    self.stdout.write(f"❌ Exercise not found: {video_data['exercise_id']}")
            
            self.stdout.write(f"✅ Created {created_videos} video clips")
        
        # Final stats
        total_exercises = Exercise.objects.count()
        total_videos = VideoClip.objects.count()
        
        self.stdout.write(f"\\n🎉 INDEXING COMPLETE!")
        self.stdout.write(f"   💪 Total exercises: {total_exercises}")
        self.stdout.write(f"   🎬 Total videos: {total_videos}")
        
        return f"Indexed {total_exercises} exercises and {total_videos} videos"