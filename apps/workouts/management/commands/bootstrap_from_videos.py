import os
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.workouts.models import Exercise, VideoClip

class Command(BaseCommand):
    help = 'Bootstrap entire application from video files on disk - FRESH START'

    def add_arguments(self, parser):
        parser.add_argument('--media-path', type=str, default='/opt/render/project/src/media/videos',
                          help='Path to video files')
        parser.add_argument('--dry-run', action='store_true',
                          help='Show what would be created without saving')

    def handle(self, *args, **options):
        media_path = options['media_path']
        dry_run = options['dry_run']
        
        self.stdout.write("🚀 BOOTSTRAPPING AI FITNESS COACH FROM VIDEOS")
        self.stdout.write("=" * 60)
        
        if not os.path.exists(media_path):
            self.stdout.write(f"❌ Media path not found: {media_path}")
            return
        
        exercises_dir = os.path.join(media_path, 'exercises')
        if not os.path.exists(exercises_dir):
            self.stdout.write(f"❌ Exercises directory not found: {exercises_dir}")
            return
        
        # Get all exercise directories
        exercise_dirs = sorted([d for d in os.listdir(exercises_dir) 
                               if os.path.isdir(os.path.join(exercises_dir, d)) and d.startswith('EX')])
        
        self.stdout.write(f"📁 Found {len(exercise_dirs)} exercise directories")
        
        # Exercise name mapping
        exercise_names = {
            'EX001': 'Push-ups', 'EX002': 'Squats', 'EX003': 'Pull-ups', 'EX004': 'Lunges',
            'EX005': 'Plank', 'EX006': 'Deadlifts', 'EX007': 'Bench Press', 'EX008': 'Rows',
            'EX009': 'Burpees', 'EX010': 'Mountain Climbers', 'EX011': 'Jumping Jacks', 
            'EX012': 'Dips', 'EX013': 'Leg Raises', 'EX014': 'Crunches', 'EX015': 'Russian Twists',
            'EX016': 'Wall Sits', 'EX017': 'High Knees', 'EX018': 'Butt Kicks', 'EX019': 'Jump Rope',
            'EX020': 'Box Jumps', 'EX021': 'Step-ups', 'EX022': 'Lateral Raises', 'EX023': 'Bicep Curls',
            'EX024': 'Tricep Extensions', 'EX025': 'Shoulder Press', 'EX026': 'Chest Flyes',
            'EX027': 'Reverse Flyes', 'EX028': 'Upright Rows', 'EX029': 'Shrugs', 'EX030': 'Face Pulls',
            'EX031': 'Hammer Curls', 'EX032': 'Concentration Curls', 'EX033': 'Preacher Curls',
            'EX034': 'Cable Curls', 'EX035': 'Overhead Press', 'EX036': 'Arnold Press',
            'EX037': 'Lateral Raises', 'EX038': 'Front Raises', 'EX039': 'Rear Delt Flyes',
            'EX040': 'Pike Push-ups', 'EX041': 'Handstand Push-ups', 'EX042': 'Diamond Push-ups',
            'EX043': 'Wide Push-ups', 'EX044': 'Decline Push-ups', 'EX045': 'Incline Push-ups',
            'EX046': 'Hindu Push-ups', 'EX047': 'Archer Push-ups', 'EX048': 'One-arm Push-ups',
            'EX049': 'Clap Push-ups', 'EX050': 'Bulgarian Split Squats', 'EX051': 'Goblet Squats',
            'EX052': 'Jump Squats', 'EX053': 'Pistol Squats', 'EX054': 'Sumo Squats',
            'EX055': 'Cossack Squats', 'EX056': 'Single Leg Deadlifts', 'EX057': 'Romanian Deadlifts',
            'EX058': 'Stiff Leg Deadlifts', 'EX059': 'Deficit Deadlifts', 'EX060': 'Rack Pulls',
            'EX061': 'Good Mornings', 'EX062': 'Hip Thrusts', 'EX063': 'Glute Bridges',
            'EX064': 'Calf Raises', 'EX065': 'Single Leg Calf Raises', 'EX066': 'Seated Calf Raises',
            'EX067': 'Leg Curls', 'EX068': 'Leg Extensions', 'EX069': 'Leg Press',
            'EX070': 'Walking Lunges', 'EX071': 'Reverse Lunges', 'EX072': 'Side Lunges',
            'EX073': 'Curtsy Lunges', 'EX074': 'Clock Lunges', 'EX075': 'Jump Lunges',
            'EX076': 'Chest Press', 'EX077': 'Incline Press', 'EX078': 'Decline Press',
            'EX079': 'Dumbbell Press', 'EX080': 'Dumbbell Flyes', 'EX081': 'Cable Crossovers',
            'EX082': 'Pec Deck', 'EX083': 'T-Bar Rows', 'EX084': 'Cable Rows',
            'EX085': 'Lat Pulldowns', 'EX086': 'Wide Grip Pull-ups', 'EX087': 'Chin-ups',
            'EX088': 'Inverted Rows', 'EX089': 'Single Arm Rows', 'EX090': 'Bent Over Rows',
            'EX091': 'Pendlay Rows', 'EX092': 'Meadows Rows', 'EX093': 'Seal Rows',
            'EX094': 'Chest Supported Rows', 'EX095': 'Machine Rows', 'EX096': 'Resistance Band Rows',
            'EX097': 'TRX Rows', 'EX098': 'Landmine Rows', 'EX099': 'Renegade Rows',
            'EX100': 'Gorilla Rows'
        }
        
        # Muscle group mapping
        muscle_groups_map = {
            'EX001': ['chest', 'arms'], 'EX002': ['legs'], 'EX003': ['back', 'arms'], 'EX004': ['legs'],
            'EX005': ['core'], 'EX006': ['back', 'legs'], 'EX007': ['chest', 'arms'], 'EX008': ['back', 'arms'],
            'EX009': ['full_body'], 'EX010': ['core', 'legs'], 'EX011': ['full_body'], 'EX012': ['chest', 'arms'],
            'EX013': ['core'], 'EX014': ['core'], 'EX015': ['core'], 'EX016': ['legs'],
            'EX017': ['legs'], 'EX018': ['legs'], 'EX019': ['full_body'], 'EX020': ['legs'],
            'EX021': ['legs'], 'EX022': ['shoulders'], 'EX023': ['arms'], 'EX024': ['arms'],
            'EX025': ['shoulders'], 'EX026': ['chest'], 'EX027': ['back'], 'EX028': ['shoulders'],
            'EX029': ['shoulders'], 'EX030': ['back'], 'EX031': ['arms'], 'EX032': ['arms'],
            'EX033': ['arms'], 'EX034': ['arms'], 'EX035': ['shoulders'], 'EX036': ['shoulders'],
            'EX037': ['shoulders'], 'EX038': ['shoulders'], 'EX039': ['shoulders'], 'EX040': ['shoulders'],
            'EX041': ['shoulders'], 'EX042': ['chest', 'arms'], 'EX043': ['chest'], 'EX044': ['chest'],
            'EX045': ['chest'], 'EX046': ['chest', 'shoulders'], 'EX047': ['chest'], 'EX048': ['chest'],
            'EX049': ['chest'], 'EX050': ['legs'], 'EX051': ['legs'], 'EX052': ['legs'],
            'EX053': ['legs'], 'EX054': ['legs'], 'EX055': ['legs'], 'EX056': ['back', 'legs'],
            'EX057': ['back', 'legs'], 'EX058': ['back', 'legs'], 'EX059': ['back', 'legs'], 
            'EX060': ['back'], 'EX061': ['back', 'legs'], 'EX062': ['legs'], 'EX063': ['legs'],
            'EX064': ['legs'], 'EX065': ['legs'], 'EX066': ['legs'], 'EX067': ['legs'],
            'EX068': ['legs'], 'EX069': ['legs'], 'EX070': ['legs'], 'EX071': ['legs'],
            'EX072': ['legs'], 'EX073': ['legs'], 'EX074': ['legs'], 'EX075': ['legs'],
            'EX076': ['chest'], 'EX077': ['chest'], 'EX078': ['chest'], 'EX079': ['chest'],
            'EX080': ['chest'], 'EX081': ['chest'], 'EX082': ['chest'], 'EX083': ['back'],
            'EX084': ['back'], 'EX085': ['back'], 'EX086': ['back', 'arms'], 'EX087': ['back', 'arms'],
            'EX088': ['back'], 'EX089': ['back'], 'EX090': ['back'], 'EX091': ['back'],
            'EX092': ['back'], 'EX093': ['back'], 'EX094': ['back'], 'EX095': ['back'],
            'EX096': ['back'], 'EX097': ['back'], 'EX098': ['back'], 'EX099': ['back', 'core'],
            'EX100': ['back']
        }
        
        exercises_data = {}
        videos_data = []
        
        for ex_dir in exercise_dirs:
            exercise_path = os.path.join(exercises_dir, ex_dir)
            video_files = [f for f in os.listdir(exercise_path) if f.endswith('.mp4')]
            
            if not video_files:
                continue
            
            # Create exercise
            exercise_name = exercise_names.get(ex_dir, f'Exercise {ex_dir}')
            muscle_groups = muscle_groups_map.get(ex_dir, ['full_body'])
            
            exercises_data[ex_dir] = {
                'id': ex_dir,
                'slug': ex_dir.lower(),
                'name': exercise_name,
                'description': f'{exercise_name} - proper form and technique',
                'difficulty': 'beginner',
                'muscle_groups': muscle_groups,
                'equipment_needed': [],
                'is_active': True
            }
            
            # Process videos
            for video_file in video_files:
                match = re.match(r'^(.+?)_(.+?)\\.mp4$', video_file)
                if match:
                    video_type = match.group(1)  # technique, mistake
                    model_name = match.group(2)  # mod1
                    
                    if video_type in ['technique', 'mistake']:
                        video_path = os.path.join(exercise_path, video_file)
                        relative_path = os.path.relpath(video_path, '/opt/render/project/src')
                        
                        videos_data.append({
                            'exercise_id': ex_dir,
                            'type': video_type,
                            'archetype': 'bro',  # Default
                            'model_name': model_name,
                            'file_url': f'/{relative_path}',
                            'duration_seconds': 30  # Default
                        })
        
        # Show stats
        self.stdout.write(f"\\n📊 BOOTSTRAP RESULTS:")
        self.stdout.write(f"   💪 Exercises: {len(exercises_data)}")
        self.stdout.write(f"   🎬 Videos: {len(videos_data)}")
        
        type_stats = {}
        for video in videos_data:
            type_stats[video['type']] = type_stats.get(video['type'], 0) + 1
        
        self.stdout.write(f"\\n📈 VIDEO DISTRIBUTION:")
        for vtype, count in sorted(type_stats.items()):
            self.stdout.write(f"   {vtype}: {count}")
        
        if dry_run:
            self.stdout.write(f"\\n🔍 DRY RUN - Would create:")
            self.stdout.write(f"   💪 {len(exercises_data)} exercises")
            self.stdout.write(f"   🎬 {len(videos_data)} video clips")
            return
        
        # CLEAN START - Clear everything
        self.stdout.write(f"\\n🗑️ CLEARING OLD DATA...")
        with transaction.atomic():
            VideoClip.objects.all().delete()
            Exercise.objects.all().delete()
            
            # Create exercises
            self.stdout.write(f"💪 Creating {len(exercises_data)} exercises...")
            for ex_id, ex_data in exercises_data.items():
                Exercise.objects.create(**ex_data)
            
            # Create videos
            self.stdout.write(f"🎬 Creating {len(videos_data)} video clips...")
            for video_data in videos_data:
                exercise = Exercise.objects.get(id=video_data['exercise_id'])
                VideoClip.objects.create(
                    exercise=exercise,
                    type=video_data['type'],
                    archetype=video_data['archetype'],
                    model_name=video_data['model_name'],
                    url=video_data['file_url'],
                    duration_seconds=video_data['duration_seconds'],
                    is_active=True
                )
        
        # Final stats
        final_exercises = Exercise.objects.count()
        final_videos = VideoClip.objects.count()
        
        self.stdout.write(f"\\n🎉 BOOTSTRAP COMPLETE!")
        self.stdout.write(f"   💪 Total exercises: {final_exercises}")
        self.stdout.write(f"   🎬 Total videos: {final_videos}")
        self.stdout.write(f"   🚀 AI Fitness Coach is ready!")
        
        return f"Bootstrapped {final_exercises} exercises and {final_videos} videos"