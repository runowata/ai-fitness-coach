"""
Smoke test command to verify v2 readiness
"""
import json

from django.core.management.base import BaseCommand
from django.db import connection

from apps.ai_integration.prompt_manager_v2 import PromptManagerV2
from apps.core.services.exercise_validation import ExerciseValidationService
from apps.workouts.models import CSVExercise, VideoClip, WorkoutPlan
from apps.workouts.services.playlist_v2 import build_playlist


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
        
        # 2. Check exercise coverage
        self.stdout.write("\n2️⃣ Checking exercise video coverage...")
        try:
            service = ExerciseValidationService()
            allowed_slugs = service.get_allowed_exercise_slugs()
            total_exercises = CSVExercise.objects.filter(is_active=True).count()
            
            coverage_pct = (len(allowed_slugs) / total_exercises * 100) if total_exercises > 0 else 0
            
            if coverage_pct < 10:
                warnings.append(f"Low video coverage: {coverage_pct:.1f}%")
                self.stdout.write(self.style.WARNING(f"   ⚠️  Coverage: {len(allowed_slugs)}/{total_exercises} ({coverage_pct:.1f}%)"))
            else:
                self.stdout.write(self.style.SUCCESS(f"   ✅ Coverage: {len(allowed_slugs)}/{total_exercises} ({coverage_pct:.1f}%)"))
            
            if verbose:
                report = service.get_coverage_report()
                stats = report.get('statistics', {})
                self.stdout.write(f"      Complete: {stats.get('complete', 0)}")
                self.stdout.write(f"      Partial: {stats.get('partial', 0)}")
                self.stdout.write(f"      None: {stats.get('none', 0)}")
                
        except Exception as e:
            errors.append(f"Coverage check failed: {e}")
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
                    
                    # 4. Test playlist generation
                    self.stdout.write("\n4️⃣ Testing playlist generation...")
                    archetype = getattr(plan.user.profile, 'archetype', 'mentor') if hasattr(plan.user, 'profile') else 'mentor'
                    playlist = build_playlist(plan.plan_data, archetype)
                    
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
        
        # 5. Check database indexes
        self.stdout.write("\n5️⃣ Checking database indexes...")
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'video_clips'
                    AND indexname LIKE '%r2_kind%'
                """)
                indexes = cursor.fetchall()
                
                if len(indexes) < 2:
                    warnings.append("Missing r2_kind indexes on video_clips")
                    self.stdout.write(self.style.WARNING(f"   ⚠️  Found {len(indexes)} r2_kind indexes (expected 2+)"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"   ✅ Found {len(indexes)} r2_kind indexes"))
                    
        except Exception as e:
            warnings.append(f"Index check failed: {e}")
            self.stdout.write(self.style.WARNING(f"   ⚠️  Could not check indexes: {e}"))
        
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