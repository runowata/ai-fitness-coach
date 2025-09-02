"""
Management command to cleanup legacy v1 columns that may remain after migration
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Force cleanup of legacy v1 columns from database'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🧹 Cleaning up legacy v1 columns..."))
        
        with connection.cursor() as cursor:
            # Remove legacy columns from exercises table
            legacy_exercise_columns = ['mistake_video_url', 'technique_video_url']
            
            for column in legacy_exercise_columns:
                try:
                    # Check if column exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name='workouts_exercise' AND column_name=%s
                        )
                    """, [column])
                    
                    if cursor.fetchone()[0]:
                        self.stdout.write(f"  🗑️  Dropping {column} from workouts_exercise...")
                        cursor.execute(f"ALTER TABLE workouts_exercise DROP COLUMN {column}")
                        self.stdout.write(self.style.SUCCESS(f"    ✅ Dropped {column}"))
                    else:
                        self.stdout.write(f"    ✓ {column} already removed")
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"    ❌ Error dropping {column}: {e}"))
            
            # Remove legacy columns from video_clips table
            legacy_videoclip_columns = ['type', 'url']
            
            for column in legacy_videoclip_columns:
                try:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name='video_clips' AND column_name=%s
                        )
                    """, [column])
                    
                    if cursor.fetchone()[0]:
                        self.stdout.write(f"  🗑️  Dropping {column} from video_clips...")
                        cursor.execute(f"ALTER TABLE video_clips DROP COLUMN {column}")
                        self.stdout.write(self.style.SUCCESS(f"    ✅ Dropped {column}"))
                    else:
                        self.stdout.write(f"    ✓ {column} already removed")
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"    ❌ Error dropping {column}: {e}"))
        
        self.stdout.write(self.style.SUCCESS("\n🎉 Legacy column cleanup completed!"))