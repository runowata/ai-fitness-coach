from django.core.management.base import BaseCommand
from django.db import transaction

from apps.workouts.models import CSVExercise, VideoClip


class Command(BaseCommand):
    help = 'Create placeholder video clips for all exercises'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                          help='Show what would be created without saving')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("🎬 CREATING PLACEHOLDER VIDEO CLIPS")
        self.stdout.write("=" * 60)
        
        exercises = CSVExercise.objects.all()
        archetypes = ['bro', 'sergeant', 'intellectual']
        video_types = ['technique', 'mistake']
        
        videos_to_create = []
        
        for exercise in exercises:
            for archetype in archetypes:
                for video_type in video_types:
                    videos_to_create.append({
                        'exercise': exercise,
                        'type': video_type,
                        'archetype': archetype,
                        'model_name': 'mod1',
                        'url': '/static/videos/placeholder.mp4',
                        'duration_seconds': 30,
                        'is_active': True,
                        'is_placeholder': True  # Mark as placeholder for filtering
                    })
        
        self.stdout.write(f"📊 Will create {len(videos_to_create)} video clips")
        self.stdout.write(f"   📹 For {exercises.count()} exercises")
        self.stdout.write(f"   👥 Across {len(archetypes)} archetypes")
        self.stdout.write(f"   🎭 With {len(video_types)} video types each")
        
        if dry_run:
            self.stdout.write("\n🔍 DRY RUN - Would create:")
            sample = videos_to_create[:5]
            for video in sample:
                self.stdout.write(f"   {video['exercise'].id}: {video['type']} ({video['archetype']})")
            if len(videos_to_create) > 5:
                self.stdout.write(f"   ... and {len(videos_to_create) - 5} more")
            return
        
        # Create video clips
        with transaction.atomic():
            # Clear existing video clips
            self.stdout.write("🗑️ Clearing existing video clips...")
            VideoClip.objects.all().delete()
            
            # Create new video clips
            self.stdout.write(f"🎬 Creating {len(videos_to_create)} video clips...")
            created_count = 0
            
            for video_data in videos_to_create:
                VideoClip.objects.create(**video_data)
                created_count += 1
                
                if created_count % 50 == 0:
                    self.stdout.write(f"   Created {created_count}/{len(videos_to_create)} videos...")
        
        # Final verification
        final_count = VideoClip.objects.count()
        self.stdout.write("\n🎉 SUCCESS!")
        self.stdout.write(f"   🎬 Total video clips created: {final_count}")
        self.stdout.write("   📱 Video playlists will now work!")
        
        # Show distribution
        self.stdout.write("\n📊 Video distribution:")
        for archetype in archetypes:
            count = VideoClip.objects.filter(archetype=archetype).count()
            self.stdout.write(f"   {archetype}: {count} videos")
        
        for video_type in video_types:
            count = VideoClip.objects.filter(type=video_type).count()
            self.stdout.write(f"   {video_type}: {count} videos")
        
        return f"Created {final_count} placeholder video clips"