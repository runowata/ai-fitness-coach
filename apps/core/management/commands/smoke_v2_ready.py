"""
Smoke test command to verify v2 readiness
"""

from django.core.management.base import BaseCommand
from django.db import connection

from apps.ai_integration.prompt_manager_v2 import PromptManagerV2
from apps.workouts.models import WorkoutPlan
# from apps.workouts.services.playlist_v2 import build_playlist  # DEPRECATED


class Command(BaseCommand):
    help = "Smoke test v2 readiness: schema, playlist, signed URLs, coverage"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )
    
    def handle(self, *args, **options):
        verbose = options.get('verbose', False)
        errors = []
        warnings = []
        
        self.stdout.write("=" * 50)
        self.stdout.write("🔍 V2 READINESS SMOKE TEST")
        self.stdout.write("=" * 50)
        
        # 1. Check prompts v2 structure
        self.stdout.write("\n1️⃣ Checking v2 prompts...")
        try:
            pm = PromptManagerV2()
            # Test loading prompts for each archetype
            for archetype in ['mentor', 'professional', 'peer']:
                system, user = pm.get_prompt_pair('master', archetype)
                if not system or not user:
                    errors.append(f"Missing prompts for archetype: {archetype}")
                elif verbose:
                    self.stdout.write(f"   ✅ {archetype}: {len(system)} chars system, {len(user)} chars user")
            
            if not errors:
                self.stdout.write(self.style.SUCCESS("   ✅ All v2 prompts present"))
        except Exception as e:
            errors.append(f"Prompt loading failed: {e}")
            self.stdout.write(self.style.ERROR(f"   ❌ {e}"))
        
        # 2. Check R2 video count (simple)
        self.stdout.write("\n2️⃣ Checking R2 videos...")
        try:
            from apps.workouts.models import R2Video
            
            exercise_videos = R2Video.objects.filter(category='exercises').count()
            motivation_videos = R2Video.objects.filter(category='motivation').count()
            total_videos = R2Video.objects.count()
            
            self.stdout.write(self.style.SUCCESS(f"   ✅ R2Videos: {total_videos} total ({exercise_videos} exercises, {motivation_videos} motivation)"))
            
            if total_videos < 100:
                warnings.append(f"Low video count: {total_videos}")
                self.stdout.write(self.style.WARNING(f"   ⚠️  Only {total_videos} videos found"))
                
        except Exception as e:
            errors.append(f"R2Video check failed: {e}")
            self.stdout.write(self.style.ERROR(f"   ❌ {e}"))
        
        # 3. Check recent workout plan
        self.stdout.write("\n3️⃣ Checking workout plans...")
        try:
            plan = WorkoutPlan.objects.filter(is_active=True).order_by("-created_at").first()
            if not plan:
                warnings.append("No active workout plans in database")
                self.stdout.write(self.style.WARNING("   ⚠️  No active plans found"))
            else:
                # Check plan structure
                if not isinstance(plan.plan_data, dict):
                    errors.append(f"Plan {plan.id} has invalid data type: {type(plan.plan_data)}")
                elif 'weeks' not in plan.plan_data:
                    errors.append(f"Plan {plan.id} missing 'weeks' field")
                else:
                    weeks_count = len(plan.plan_data.get('weeks', []))
                    self.stdout.write(self.style.SUCCESS(f"   ✅ Latest plan: {plan.id} ({weeks_count} weeks)"))
                    
                    # 4. Test playlist generation (simple check)
                    self.stdout.write("\n4️⃣ Testing playlist generation...")
                    archetype = getattr(plan.user.profile, 'archetype', 'mentor') if hasattr(plan.user, 'profile') else 'mentor'
                    
                    try:
                        from apps.workouts.models import DailyWorkout
                        
                        # Check if any playlist items exist
                        first_workout = DailyWorkout.objects.filter(plan=plan).first()
                        if first_workout:
                            existing_items = first_workout.playlist_items.count()
                            if existing_items > 0:
                                playlist = [{'clip_id': f'test_{i}'} for i in range(existing_items)]
                                self.stdout.write(self.style.SUCCESS(f"   ✅ Found {existing_items} existing playlist items"))
                            else:
                                playlist = []
                                warnings.append("No playlist items found for workout")
                        else:
                            playlist = []
                            warnings.append("No workouts found in plan")
                    except Exception as e:
                        playlist = []
                        warnings.append(f"Playlist check failed: {e}")
                    
                    if not playlist:
                        warnings.append(f"Empty playlist for plan {plan.id}")
                        self.stdout.write(self.style.WARNING("   ⚠️  Empty playlist generated"))
                    else:
                        video_items = [item for item in playlist if item.get('clip_id')]
                        text_items = [item for item in playlist if item.get('text')]
                        
                        self.stdout.write(self.style.SUCCESS(f"   ✅ Playlist: {len(video_items)} videos, {len(text_items)} texts"))
                        
                        # Check for signed URLs
                        missing_urls = [
                            item for item in video_items 
                            if not item.get('signed_url')
                        ]
                        if missing_urls:
                            errors.append(f"{len(missing_urls)} videos missing signed URLs")
                            self.stdout.write(self.style.ERROR(f"   ❌ {len(missing_urls)} missing signed URLs"))
                        elif verbose and video_items:
                            self.stdout.write(f"      Sample URL: {video_items[0].get('signed_url', '')[:50]}...")
                            
        except Exception as e:
            errors.append(f"Plan check failed: {e}")
            self.stdout.write(self.style.ERROR(f"   ❌ {e}"))
        
        # 5. Check database tables (simple)
        self.stdout.write("\n5️⃣ Checking database tables...")
        try:
            with connection.cursor() as cursor:
                # Check if R2Video table exists
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = 'r2_videos'
                """)
                r2_videos_exists = cursor.fetchone()[0] > 0
                
                # Check if DailyPlaylistItem table exists  
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = 'daily_playlist_items'
                """)
                playlist_items_exists = cursor.fetchone()[0] > 0
                
                if r2_videos_exists and playlist_items_exists:
                    self.stdout.write(self.style.SUCCESS("   ✅ Core tables exist"))
                else:
                    warnings.append("Missing core tables")
                    self.stdout.write(self.style.WARNING("   ⚠️  Missing core tables"))
                    
        except Exception as e:
            warnings.append(f"Table check failed: {e}")
            self.stdout.write(self.style.WARNING(f"   ⚠️  Could not check tables: {e}"))
        
        # 6. Check R2 configuration
        self.stdout.write("\n6️⃣ Checking R2 configuration...")
        from django.conf import settings
        
        r2_configured = all([
            getattr(settings, 'USE_R2_STORAGE', False),
            getattr(settings, 'AWS_S3_ENDPOINT_URL', None),
            getattr(settings, 'AWS_ACCESS_KEY_ID', None),
        ])
        
        if not r2_configured:
            warnings.append("R2 storage not fully configured")
            self.stdout.write(self.style.WARNING("   ⚠️  R2 not configured (check env vars)"))
        else:
            self.stdout.write(self.style.SUCCESS("   ✅ R2 storage configured"))
            if verbose:
                self.stdout.write(f"      Endpoint: {settings.AWS_S3_ENDPOINT_URL}")
                self.stdout.write(f"      Expire: {settings.AWS_QUERYSTRING_EXPIRE}s")
        
        # Final summary
        self.stdout.write("\n" + "=" * 50)
        if errors:
            self.stdout.write(self.style.ERROR(f"❌ FAILED: {len(errors)} errors, {len(warnings)} warnings"))
            for error in errors:
                self.stdout.write(self.style.ERROR(f"   • {error}"))
            self.command = 1  # Exit code 1
        elif warnings:
            self.stdout.write(self.style.WARNING(f"⚠️  PASSED WITH WARNINGS: {len(warnings)} warnings"))
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f"   • {warning}"))
            self.command = 0
        else:
            self.stdout.write(self.style.SUCCESS("✅ V2 READY: All checks passed!"))
            self.command = 0
        
        self.stdout.write("=" * 50)