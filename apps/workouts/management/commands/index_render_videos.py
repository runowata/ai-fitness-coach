import os
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.workouts.models import Exercise, VideoClip

class Command(BaseCommand):
    help = 'Index video files from Render disk into database'

    def add_arguments(self, parser):
        parser.add_argument('--media-path', type=str, default='/opt/render/project/src/media',
                          help='Path to media files on Render disk')
        parser.add_argument('--dry-run', action='store_true',
                          help='Show what would be created without saving')
        parser.add_argument('--clear-existing', action='store_true',
                          help='Clear existing data before indexing')

    def handle(self, *args, **options):
        media_path = options['media_path']
        dry_run = options['dry_run']
        clear_existing = options['clear_existing']
        
        self.stdout.write("🚀 INDEXING RENDER DISK VIDEOS...")
        self.stdout.write(f"📁 Scanning path: {media_path}")
        
        if not os.path.exists(media_path):
            self.stdout.write(f"❌ Media path not found: {media_path}")
            self.stdout.write("⚠️  Running locally? Using fallback paths...")
            
            # Fallback for local development
            fallback_paths = ['./media', './static/videos', 'media', 'static/videos']
            for path in fallback_paths:
                if os.path.exists(path):
                    media_path = path
                    self.stdout.write(f"✅ Using fallback path: {media_path}")
                    break
            else:
                self.stdout.write("❌ No video files found anywhere!")
                return
        
        # Recursively find all MP4 files
        video_files = []
        self.stdout.write("🔍 Scanning for MP4 files...")
        
        for root, dirs, files in os.walk(media_path):
            mp4_files = [f for f in files if f.endswith('.mp4')]
            if mp4_files:
                self.stdout.write(f"📁 {root}: {len(mp4_files)} files")
                for file in mp4_files:
                    full_path = os.path.join(root, file)
                    video_files.append(full_path)
        
        self.stdout.write(f"🎬 TOTAL MP4 FILES FOUND: {len(video_files)}")
        
        if len(video_files) == 0:
            self.stdout.write("❌ No MP4 files found!")
            return
        
        # Parse video files
        exercises_data = {}
        videos_data = []
        skipped = 0
        
        self.stdout.write("🔍 PARSING FILE NAMES...")
        
        for file_path in video_files:
            filename = os.path.basename(file_path)
            
            # Skip placeholder
            if filename == 'placeholder.mp4':
                continue
                
            # Try different naming patterns
            patterns = [
                # exercise_type_archetype_model.mp4
                r'^(.+?)_(.+?)_(.+?)_(.+?)\.mp4$',
                # exercise_type_archetype.mp4  
                r'^(.+?)_(.+?)_(.+?)\.mp4$',
                # exercise_type.mp4
                r'^(.+?)_(.+?)\.mp4$'
            ]
            
            parsed = False
            for pattern in patterns:
                match = re.match(pattern, filename)
                if match:
                    groups = match.groups()
                    if len(groups) >= 3:
                        exercise_slug = groups[0]
                        video_type = groups[1] 
                        archetype = groups[2]
                        model_name = groups[3] if len(groups) > 3 else 'mod1'
                    elif len(groups) == 2:
                        exercise_slug = groups[0]
                        video_type = groups[1]
                        archetype = 'bro'  # default
                        model_name = 'mod1'
                    
                    # Validate video type
                    valid_types = ['technique', 'mistake', 'instruction', 'reminder', 'weekly', 'final']
                    if video_type not in valid_types:
                        self.stdout.write(f"⚠️  Unknown video type '{video_type}' in {filename}")
                        continue
                    
                    # Validate archetype  
                    valid_archetypes = ['bro', 'sergeant', 'intellectual']
                    if archetype not in valid_archetypes:
                        self.stdout.write(f"⚠️  Unknown archetype '{archetype}' in {filename}")
                        continue
                    
                    # Store exercise
                    if exercise_slug not in exercises_data:
                        exercises_data[exercise_slug] = {
                            'id': exercise_slug,
                            'name': exercise_slug.replace('-', ' ').replace('_', ' ').title(),
                            'description': f'Exercise: {exercise_slug}',
                            'difficulty': 'beginner',
                            'muscle_groups': self.guess_muscle_groups(exercise_slug),
                            'equipment_needed': [],
                            'is_active': True
                        }
                    
                    # Store video
                    # Make URL relative to media root
                    relative_path = os.path.relpath(file_path, media_path)
                    video_url = f'/media/{relative_path}'
                    
                    videos_data.append({
                        'exercise_slug': exercise_slug,
                        'type': video_type,
                        'archetype': archetype, 
                        'model_name': model_name,
                        'file_url': video_url,
                        'file_path': file_path
                    })
                    
                    parsed = True
                    break
            
            if not parsed:
                self.stdout.write(f"⚠️  Skipped unparseable file: {filename}")
                skipped += 1
        
        # Show stats
        self.stdout.write(f"\n📊 PARSING RESULTS:")
        self.stdout.write(f"   💪 Exercises found: {len(exercises_data)}")
        self.stdout.write(f"   🎬 Videos parsed: {len(videos_data)}")
        self.stdout.write(f"   ⚠️  Files skipped: {skipped}")
        
        # Analyze video distribution
        type_stats = {}
        archetype_stats = {}
        for video in videos_data:
            type_stats[video['type']] = type_stats.get(video['type'], 0) + 1
            archetype_stats[video['archetype']] = archetype_stats.get(video['archetype'], 0) + 1
        
        self.stdout.write(f"\n📈 VIDEO TYPE DISTRIBUTION:")
        for vtype, count in sorted(type_stats.items()):
            self.stdout.write(f"   {vtype}: {count}")
        
        self.stdout.write(f"\n📈 ARCHETYPE DISTRIBUTION:")
        for arch, count in sorted(archetype_stats.items()):
            self.stdout.write(f"   {arch}: {count}")
        
        if dry_run:
            self.stdout.write(f"\n🔍 DRY RUN - Would create:")
            self.stdout.write(f"   💪 {len(exercises_data)} exercises")
            self.stdout.write(f"   🎬 {len(videos_data)} video clips")
            return
        
        # Save to database
        self.stdout.write(f"\n💾 SAVING TO DATABASE...")
        
        with transaction.atomic():
            if clear_existing:
                self.stdout.write("🗑️ Clearing existing data...")
                VideoClip.objects.all().delete()
                Exercise.objects.all().delete()
            
            # Create exercises
            created_exercises = 0
            for slug, ex_data in exercises_data.items():
                exercise, created = Exercise.objects.get_or_create(
                    id=slug,
                    defaults=ex_data
                )
                if created:
                    created_exercises += 1
            
            self.stdout.write(f"✅ Created {created_exercises} exercises")
            
            # Create video clips
            created_videos = 0
            for video_data in videos_data:
                try:
                    exercise = Exercise.objects.get(id=video_data['exercise_slug'])
                    
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
                    self.stdout.write(f"❌ Exercise not found: {video_data['exercise_slug']}")
            
            self.stdout.write(f"✅ Created {created_videos} video clips")
        
        # Final stats
        total_exercises = Exercise.objects.count()
        total_videos = VideoClip.objects.count()
        
        self.stdout.write(f"\n🎉 INDEXING COMPLETE!")
        self.stdout.write(f"   💪 Total exercises: {total_exercises}")
        self.stdout.write(f"   🎬 Total videos: {total_videos}")
        self.stdout.write(f"   📁 Files processed: {len(video_files)}")
    
    def guess_muscle_groups(self, exercise_slug):
        """Guess muscle groups from exercise name"""
        name_lower = exercise_slug.lower()
        
        muscle_map = {
            'push': ['chest', 'arms'],
            'pull': ['back', 'arms'],
            'squat': ['legs'],
            'deadlift': ['back', 'legs'],
            'bench': ['chest', 'arms'],
            'row': ['back', 'arms'],
            'curl': ['arms'],
            'press': ['shoulders', 'arms'],
            'plank': ['core'],
            'crunch': ['core'],
            'lunge': ['legs'],
            'dip': ['chest', 'arms'],
        }
        
        for keyword, muscles in muscle_map.items():
            if keyword in name_lower:
                return muscles
                
        return ['full_body']  # Default