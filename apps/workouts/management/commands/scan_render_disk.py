import os
import re
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Scan Render disk for video files and show structure'

    def handle(self, *args, **options):
        self.stdout.write("🚀 SCANNING RENDER DISK FOR VIDEOS...")
        
        # Render disk paths to check
        paths_to_check = [
            '/opt/render/project/src/media',
            '/opt/render/project/src/static/videos',
            './media',
            './static/videos',
            os.path.join(settings.BASE_DIR, 'media'),
            os.path.join(settings.BASE_DIR, 'static', 'videos'),
        ]
        
        total_files = 0
        video_files = []
        
        for path in paths_to_check:
            if os.path.exists(path):
                self.stdout.write(f"✅ FOUND: {path}")
                for root, dirs, files in os.walk(path):
                    mp4_files = [f for f in files if f.endswith('.mp4')]
                    if mp4_files:
                        self.stdout.write(f"📁 {root}: {len(mp4_files)} files")
                        for file in mp4_files[:5]:  # Show first 5
                            self.stdout.write(f"   📹 {file}")
                        if len(mp4_files) > 5:
                            self.stdout.write(f"   ... and {len(mp4_files)-5} more")
                        
                        for file in mp4_files:
                            video_files.append(os.path.join(root, file))
                        total_files += len(mp4_files)
            else:
                self.stdout.write(f"❌ NOT FOUND: {path}")
        
        self.stdout.write(f"\n🎯 TOTAL VIDEO FILES FOUND: {total_files}")
        
        if video_files:
            self.stdout.write("\n📊 ANALYZING FILE PATTERNS...")
            patterns = {}
            for file_path in video_files[:20]:  # Analyze first 20
                filename = os.path.basename(file_path)
                # Try to extract pattern: exercise_type_archetype_model.mp4
                match = re.match(r'(.+?)_(.+?)_(.+?)_(.+?)\.mp4', filename)
                if match:
                    exercise, video_type, archetype, model = match.groups()
                    pattern = f"{video_type}_{archetype}"
                    patterns[pattern] = patterns.get(pattern, 0) + 1
                    self.stdout.write(f"   🎬 {exercise} | {video_type} | {archetype} | {model}")
            
            self.stdout.write(f"\n📈 PATTERN STATS:")
            for pattern, count in sorted(patterns.items()):
                self.stdout.write(f"   {pattern}: {count} files")
        
        return f"Scan complete: {total_files} video files found"