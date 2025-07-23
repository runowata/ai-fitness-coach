import os
from django.core.management.base import BaseCommand
from apps.workouts.models import Exercise, VideoClip

class Command(BaseCommand):
    help = 'Scan and report video files on Render disk'

    def handle(self, *args, **options):
        self.stdout.write("🚀 RENDER VIDEO SCAN REPORT")
        self.stdout.write("=" * 50)
        
        # Scan for video files
        video_paths = [
            '/opt/render/project/src/media',
            '/opt/render/project/src/static/videos', 
            './media',
            './static/videos'
        ]
        
        total_videos = 0
        all_videos = []
        
        for base_path in video_paths:
            if os.path.exists(base_path):
                self.stdout.write(f"✅ SCANNING: {base_path}")
                for root, dirs, files in os.walk(base_path):
                    mp4_files = [f for f in files if f.endswith('.mp4')]
                    if mp4_files:
                        self.stdout.write(f"   📁 {root}: {len(mp4_files)} videos")
                        for f in mp4_files:
                            all_videos.append(os.path.join(root, f))
                        total_videos += len(mp4_files)
            else:
                self.stdout.write(f"❌ NOT FOUND: {base_path}")
        
        self.stdout.write(f"\n🎬 TOTAL VIDEOS FOUND: {total_videos}")
        
        # Database comparison
        db_exercises = Exercise.objects.count()
        db_videos = VideoClip.objects.count()
        
        self.stdout.write(f"\n💾 DATABASE STATUS:")
        self.stdout.write(f"   💪 Exercises: {db_exercises}")
        self.stdout.write(f"   🎬 VideoClips: {db_videos}")
        
        # Show file samples
        if all_videos:
            self.stdout.write(f"\n📋 SAMPLE FILES (first 10):")
            for i, video_path in enumerate(all_videos[:10]):
                filename = os.path.basename(video_path)
                self.stdout.write(f"   {i+1}. {filename}")
        
        self.stdout.write("\n" + "=" * 50)
        return f"Found {total_videos} videos, DB has {db_exercises} exercises, {db_videos} video clips"