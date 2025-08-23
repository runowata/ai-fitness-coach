"""
Management command to audit VideoClip data against R2 storage
"""
import csv
import os
import sys
from typing import List, Dict

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from apps.core.services.media import MediaService
from apps.workouts.models import VideoClip


class Command(BaseCommand):
    help = 'Audit VideoClip records against R2 storage to find missing files'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output-csv',
            type=str,
            default='video_audit_report.csv',
            help='Output CSV file for detailed report (default: video_audit_report.csv)'
        )
        parser.add_argument(
            '--fail-on-missing',
            action='store_true',
            help='Exit with error code if missing videos are found'
        )
        parser.add_argument(
            '--archetype',
            type=str,
            choices=['mentor', 'professional', 'peer'],
            help='Audit only clips for specific archetype'
        )
        parser.add_argument(
            '--kind',
            type=str,
            choices=['instruction', 'technique', 'mistake', 'intro', 'outro', 'reminder'],
            help='Audit only clips of specific kind'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🔍 Starting VideoClip audit against R2 storage..."))
        
        # Build query filters
        filters = {'is_active': True}
        if options['archetype']:
            filters['archetype'] = options['archetype']
        if options['kind']:
            filters['r2_kind'] = options['kind']
        
        # Get all active video clips
        clips = VideoClip.objects.filter(**filters).select_related('exercise')
        total_clips = clips.count()
        
        if options['verbose']:
            self.stdout.write(f"Auditing {total_clips} video clips...")
        
        # Audit results
        missing_files = []
        invalid_clips = []
        valid_clips = 0
        
        for clip in clips:
            try:
                # Check if clip has R2 file reference
                if not clip.r2_file:
                    invalid_clips.append({
                        'clip_id': clip.id,
                        'exercise': clip.exercise.id if clip.exercise else 'N/A',
                        'r2_kind': clip.r2_kind,
                        'archetype': clip.archetype,
                        'model_name': clip.model_name,
                        'issue': 'NO_R2_FILE_REFERENCE',
                        'r2_file': ''
                    })
                    continue
                
                # Check if file exists in R2
                try:
                    file_exists = self._check_r2_file_exists(clip)
                    if not file_exists:
                        missing_files.append({
                            'clip_id': clip.id,
                            'exercise': clip.exercise.id if clip.exercise else 'N/A',
                            'r2_kind': clip.r2_kind,
                            'archetype': clip.archetype,
                            'model_name': clip.model_name,
                            'issue': 'FILE_NOT_FOUND_IN_R2',
                            'r2_file': str(clip.r2_file)
                        })
                    else:
                        valid_clips += 1
                        if options['verbose']:
                            self.stdout.write(f"✅ {clip.id}: {clip.r2_file}")
                
                except Exception as e:
                    invalid_clips.append({
                        'clip_id': clip.id,
                        'exercise': clip.exercise.id if clip.exercise else 'N/A',
                        'r2_kind': clip.r2_kind,
                        'archetype': clip.archetype,
                        'model_name': clip.model_name,
                        'issue': f'R2_CHECK_ERROR: {str(e)}',
                        'r2_file': str(clip.r2_file)
                    })
            
            except Exception as e:
                self.stderr.write(f"Error processing clip {clip.id}: {e}")
        
        # Generate report
        self._generate_report(
            missing_files, 
            invalid_clips, 
            valid_clips, 
            total_clips, 
            options['output_csv'],
            options['verbose']
        )
        
        # Determine exit status
        total_issues = len(missing_files) + len(invalid_clips)
        if total_issues > 0:
            self.stderr.write(self.style.ERROR(
                f"❌ AUDIT FAILED: {total_issues} video clips have issues"
            ))
            self.stderr.write(f"   • {len(missing_files)} files missing from R2 storage")
            self.stderr.write(f"   • {len(invalid_clips)} clips with invalid references")
            self.stderr.write(f"   • Report saved to: {options['output_csv']}")
            
            if options['fail_on_missing']:
                sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS(
                f"✅ AUDIT PASSED: All {total_clips} video clips are valid"
            ))
    
    def _check_r2_file_exists(self, clip: VideoClip) -> bool:
        """
        Check if the R2 file exists for a video clip
        
        Args:
            clip: VideoClip instance
            
        Returns:
            bool: True if file exists in R2 storage
        """
        try:
            # Try to get a signed URL - this will fail if file doesn't exist
            signed_url = MediaService.get_signed_url(clip.r2_file)
            return bool(signed_url)
        except Exception:
            # If we can't get a signed URL, file probably doesn't exist
            return False
    
    def _generate_report(
        self, 
        missing_files: List[Dict], 
        invalid_clips: List[Dict], 
        valid_clips: int,
        total_clips: int,
        output_csv: str,
        verbose: bool = False
    ):
        """Generate detailed CSV report of audit results"""
        
        all_issues = missing_files + invalid_clips
        
        if all_issues:
            # Write CSV report
            with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['clip_id', 'exercise', 'r2_kind', 'archetype', 'model_name', 'issue', 'r2_file']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for issue in all_issues:
                    writer.writerow(issue)
            
            self.stdout.write(f"📊 Detailed report saved to: {output_csv}")
        
        # Summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write("📊 AUDIT SUMMARY")
        self.stdout.write("="*60)
        self.stdout.write(f"Total clips audited: {total_clips}")
        self.stdout.write(f"Valid clips: {valid_clips}")
        self.stdout.write(f"Missing from R2: {len(missing_files)}")
        self.stdout.write(f"Invalid references: {len(invalid_clips)}")
        self.stdout.write(f"Success rate: {(valid_clips/total_clips)*100:.1f}%")
        
        if verbose and all_issues:
            self.stdout.write("\n📋 ISSUES BREAKDOWN:")
            issue_types = {}
            for issue in all_issues:
                issue_type = issue['issue']
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
            
            for issue_type, count in sorted(issue_types.items()):
                self.stdout.write(f"  • {issue_type}: {count}")