"""
Management command to sync exercise IDs with R2 video file basenames
"""
import os
import csv
from typing import List, Dict, Tuple

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.workouts.models import CSVExercise, VideoClip


class Command(BaseCommand):
    help = 'Sync exercise IDs with R2 video file basenames and detect mismatches'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Automatically fix mismatched exercise IDs based on filenames'
        )
        parser.add_argument(
            '--output-csv',
            type=str,
            default='slug_sync_report.csv',
            help='Output CSV file for detailed report (default: slug_sync_report.csv)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🔍 Starting exercise slug synchronization..."))
        
        # Analyze mismatches
        mismatches = self._analyze_slug_mismatches()
        
        if not mismatches:
            self.stdout.write(self.style.SUCCESS(
                "✅ All exercise IDs match their video file basenames"
            ))
            return
        
        # Generate report
        self._generate_report(mismatches, options['output_csv'])
        
        # Show summary
        self.stdout.write(f"\n📊 Found {len(mismatches)} slug mismatches")
        
        if options['verbose']:
            self._show_detailed_mismatches(mismatches[:10])  # Show first 10
        
        # Handle fixes if requested
        if options['fix']:
            if options['dry_run']:
                self.stdout.write(self.style.WARNING(
                    "🔸 DRY RUN: Would fix the following mismatches:"
                ))
                self._show_proposed_fixes(mismatches)
            else:
                self._apply_fixes(mismatches)
        elif not options['dry_run']:
            self.stdout.write(self.style.WARNING(
                f"💡 Use --fix to automatically correct these mismatches"
            ))
            self.stdout.write(f"💡 Use --dry-run --fix to preview changes first")
    
    def _analyze_slug_mismatches(self) -> List[Dict]:
        """
        Analyze all video clips for exercise ID/filename mismatches
        
        Returns:
            List of mismatch records
        """
        mismatches = []
        
        # Get all video clips with R2 files
        clips = VideoClip.objects.filter(
            is_active=True,
            r2_file__isnull=False
        ).exclude(r2_file='').select_related('exercise')
        
        for clip in clips:
            if not clip.exercise or not clip.r2_file:
                continue
            
            # Extract basename from R2 file path
            filename = os.path.basename(str(clip.r2_file))
            basename = os.path.splitext(filename)[0]
            
            # Parse exercise slug from filename
            # Expected format: {exercise_slug}_{kind}_{model} or variations
            file_exercise_slug = self._extract_exercise_slug_from_filename(basename)
            
            if file_exercise_slug and file_exercise_slug != clip.exercise.id:
                # Check if target exercise exists
                target_exercise_exists = CSVExercise.objects.filter(
                    id=file_exercise_slug, 
                    is_active=True
                ).exists()
                
                mismatches.append({
                    'clip_id': clip.id,
                    'current_exercise_id': clip.exercise.id,
                    'file_exercise_slug': file_exercise_slug,
                    'target_exercise_exists': target_exercise_exists,
                    'r2_kind': clip.r2_kind,
                    'archetype': clip.archetype,
                    'model_name': clip.model_name,
                    'filename': filename,
                    'can_fix': target_exercise_exists
                })
        
        return mismatches
    
    def _extract_exercise_slug_from_filename(self, basename: str) -> str:
        """
        Extract exercise slug from video filename
        
        Expected formats:
        - {exercise_slug}_technique_{model}
        - {exercise_slug}_mistake_{model}
        - {exercise_slug}_instruction_{archetype}_{model}
        - {exercise_slug}_reminder_{archetype}_{number}
        """
        parts = basename.split('_')
        
        # Handle different filename patterns
        if len(parts) >= 2:
            # Most common: exercise_slug is first part
            potential_slug = parts[0]
            
            # Validate it looks like an exercise slug (EX### format)
            if potential_slug.startswith('EX') and len(potential_slug) >= 4:
                return potential_slug
            
            # Try first two parts combined (for complex slugs)
            if len(parts) >= 3:
                combined_slug = f"{parts[0]}_{parts[1]}"
                if combined_slug.startswith('EX'):
                    return combined_slug
        
        return ""
    
    def _generate_report(self, mismatches: List[Dict], output_csv: str):
        """Generate detailed CSV report of mismatches"""
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'clip_id', 'current_exercise_id', 'file_exercise_slug', 
                'target_exercise_exists', 'can_fix', 'r2_kind', 
                'archetype', 'model_name', 'filename'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for mismatch in mismatches:
                writer.writerow(mismatch)
        
        self.stdout.write(f"📊 Detailed report saved to: {output_csv}")
    
    def _show_detailed_mismatches(self, mismatches: List[Dict]):
        """Show detailed mismatch information"""
        
        self.stdout.write("\n📋 SAMPLE MISMATCHES:")
        for mismatch in mismatches:
            status = "✅ Can fix" if mismatch['can_fix'] else "❌ Cannot fix"
            self.stdout.write(
                f"  • Clip {mismatch['clip_id']}: "
                f"{mismatch['current_exercise_id']} → {mismatch['file_exercise_slug']} "
                f"({status})"
            )
            self.stdout.write(f"    File: {mismatch['filename']}")
    
    def _show_proposed_fixes(self, mismatches: List[Dict]):
        """Show what fixes would be applied"""
        
        fixable = [m for m in mismatches if m['can_fix']]
        unfixable = [m for m in mismatches if not m['can_fix']]
        
        self.stdout.write(f"\n✅ FIXABLE MISMATCHES ({len(fixable)}):")
        for mismatch in fixable[:10]:  # Show first 10
            self.stdout.write(
                f"  • Clip {mismatch['clip_id']}: "
                f"{mismatch['current_exercise_id']} → {mismatch['file_exercise_slug']}"
            )
        
        if len(fixable) > 10:
            self.stdout.write(f"  ... and {len(fixable) - 10} more")
        
        if unfixable:
            self.stdout.write(f"\n❌ UNFIXABLE MISMATCHES ({len(unfixable)}):")
            self.stdout.write("  (Target exercises don't exist in database)")
            for mismatch in unfixable[:5]:  # Show first 5
                self.stdout.write(
                    f"  • Clip {mismatch['clip_id']}: "
                    f"{mismatch['current_exercise_id']} → {mismatch['file_exercise_slug']} "
                    f"(missing)"
                )
    
    @transaction.atomic
    def _apply_fixes(self, mismatches: List[Dict]):
        """Apply fixes to mismatched exercise IDs"""
        
        fixable = [m for m in mismatches if m['can_fix']]
        
        if not fixable:
            self.stdout.write(self.style.WARNING(
                "❌ No fixable mismatches found"
            ))
            return
        
        self.stdout.write(f"🔧 Applying fixes to {len(fixable)} video clips...")
        
        fixes_applied = 0
        errors = []
        
        for mismatch in fixable:
            try:
                # Get the clip and target exercise
                clip = VideoClip.objects.get(id=mismatch['clip_id'])
                target_exercise = CSVExercise.objects.get(id=mismatch['file_exercise_slug'])
                
                # Update the exercise reference
                old_exercise_id = clip.exercise.id
                clip.exercise = target_exercise
                clip.save(update_fields=['exercise'])
                
                fixes_applied += 1
                self.stdout.write(
                    f"  ✅ Clip {clip.id}: {old_exercise_id} → {target_exercise.id}"
                )
                
            except Exception as e:
                error_msg = f"Failed to fix clip {mismatch['clip_id']}: {e}"
                errors.append(error_msg)
                self.stderr.write(f"  ❌ {error_msg}")
        
        # Summary
        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 SYNC COMPLETE: {fixes_applied} fixes applied"
        ))
        
        if errors:
            self.stderr.write(self.style.ERROR(
                f"❌ {len(errors)} fixes failed"
            ))