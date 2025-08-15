"""
Check catalog integrity - ensure all exercises have videos and consistent slugs
"""
import logging
from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from apps.workouts.models import CSVExercise, VideoClip
from apps.core.utils.slug import normalize_exercise_slug

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check exercise catalog integrity and video coverage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix issues (normalize slugs)',
        )

    def handle(self, *args, **options):
        self.stdout.write("\n🔍 CATALOG INTEGRITY CHECK\n" + "="*50)
        
        fix_mode = options.get('fix', False)
        issues = []
        
        # 1. Check exercises without videos
        self.stdout.write("\n📹 Checking video coverage...")
        exercises_without_videos = CSVExercise.objects.filter(
            is_active=True
        ).annotate(
            video_count=Count('video_clips')
        ).filter(video_count=0)
        
        if exercises_without_videos.exists():
            self.stdout.write(
                self.style.WARNING(
                    f"❌ {exercises_without_videos.count()} exercises without videos:"
                )
            )
            for ex in exercises_without_videos[:10]:
                self.stdout.write(f"   - {ex.id}: {ex.name_ru}")
                issues.append(f"No video: {ex.id}")
        else:
            self.stdout.write(self.style.SUCCESS("✅ All exercises have videos"))
        
        # 2. Check slug normalization
        self.stdout.write("\n🏷️ Checking slug consistency...")
        slug_issues = []
        
        for exercise in CSVExercise.objects.filter(is_active=True):
            expected_slug = normalize_exercise_slug(exercise.id)
            if exercise.id != expected_slug:
                slug_issues.append({
                    'current': exercise.id,
                    'expected': expected_slug,
                    'name': exercise.name_ru
                })
        
        if slug_issues:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ {len(slug_issues)} exercises need slug normalization:"
                )
            )
            for issue in slug_issues[:10]:
                self.stdout.write(
                    f"   - {issue['current']} → {issue['expected']} ({issue['name']})"
                )
                
            if fix_mode:
                self.stdout.write("\n🔧 Fixing slugs...")
                fixed = 0
                for issue in slug_issues:
                    try:
                        exercise = CSVExercise.objects.get(id=issue['current'])
                        # Check if normalized slug already exists
                        if not CSVExercise.objects.filter(id=issue['expected']).exists():
                            exercise.id = issue['expected']
                            exercise.save()
                            fixed += 1
                            self.stdout.write(f"   Fixed: {issue['current']} → {issue['expected']}")
                        else:
                            self.stdout.write(
                                self.style.ERROR(
                                    f"   Conflict: {issue['expected']} already exists"
                                )
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"   Error fixing {issue['current']}: {e}")
                        )
                
                self.stdout.write(self.style.SUCCESS(f"✅ Fixed {fixed} slugs"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ All slugs are normalized"))
        
        # 3. Check orphaned videos
        self.stdout.write("\n🗑️ Checking orphaned videos...")
        orphaned_videos = VideoClip.objects.filter(
            exercise__isnull=True
        ).exclude(r2_kind__in=['intro', 'closing', 'weekly', 'motivation'])
        
        if orphaned_videos.exists():
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ {orphaned_videos.count()} orphaned videos found"
                )
            )
            issues.append(f"Orphaned videos: {orphaned_videos.count()}")
        else:
            self.stdout.write(self.style.SUCCESS("✅ No orphaned videos"))
        
        # 4. Check video distribution by archetype
        self.stdout.write("\n👥 Checking archetype coverage...")
        archetypes = ['mentor', 'professional', 'peer']
        
        for archetype in archetypes:
            count = VideoClip.objects.filter(
                r2_archetype=archetype,
                exercise__isnull=False
            ).values('exercise').distinct().count()
            
            total_exercises = CSVExercise.objects.filter(is_active=True).count()
            coverage = (count / total_exercises * 100) if total_exercises > 0 else 0
            
            if coverage < 80:
                self.stdout.write(
                    self.style.WARNING(
                        f"   {archetype}: {count}/{total_exercises} ({coverage:.1f}%)"
                    )
                )
                issues.append(f"Low coverage for {archetype}: {coverage:.1f}%")
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"   {archetype}: {count}/{total_exercises} ({coverage:.1f}%)"
                    )
                )
        
        # 5. Summary
        self.stdout.write("\n" + "="*50)
        if issues:
            self.stdout.write(
                self.style.WARNING(f"⚠️ CATALOG HAS {len(issues)} ISSUES")
            )
            if not fix_mode:
                self.stdout.write("\nRun with --fix to attempt automatic fixes")
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ CATALOG INTEGRITY CHECK PASSED")
            )
        
        return "\n".join(issues) if issues else "OK"