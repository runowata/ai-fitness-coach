"""
Management command to import motivational cards from R2 storage paths
Solves the issue of repeating backgrounds by importing all 1000+ available cards
"""
import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.onboarding.models import MotivationalCard


class Command(BaseCommand):
    help = "Import (or activate) MotivationalCard entries from R2 paths"

    def add_arguments(self, parser):
        parser.add_argument(
            "--from-r2-state", 
            action="store_true",
            help="Import from r2_upload_state.json file"
        )
        parser.add_argument(
            "--file", 
            help="Path to a text file with one R2 path per line"
        )
        parser.add_argument(
            "--deactivate-missing", 
            action="store_true",
            help="Deactivate cards not present in the import source"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true", 
            help="Show what would be imported without making changes"
        )

    def handle(self, *args, **opts):
        """Import motivational cards from various sources"""
        paths_to_import = set()
        
        # Source 1: R2 upload state file
        if opts["from_r2_state"]:
            r2_paths = self._load_from_r2_state()
            paths_to_import.update(r2_paths)
            self.stdout.write(f"Loaded {len(r2_paths)} paths from R2 state file")
        
        # Source 2: Text file with paths
        if opts["file"]:
            file_paths = self._load_from_file(opts["file"])
            paths_to_import.update(file_paths)
            self.stdout.write(f"Loaded {len(file_paths)} paths from {opts['file']}")
        
        # Default: Use R2 state file if no source specified
        if not paths_to_import:
            r2_paths = self._load_from_r2_state()
            paths_to_import.update(r2_paths)
            self.stdout.write(f"Using default R2 state source: {len(r2_paths)} paths")
        
        if not paths_to_import:
            self.stdout.write(self.style.ERROR("No paths found to import"))
            return
        
        # Filter for motivational cards (photos/quotes, photos/cards, etc.)
        motivational_paths = {
            path for path in paths_to_import 
            if any(pattern in path for pattern in [
                'photos/quotes/', 
                'photos/cards/', 
                'images/cards/',
                'card_quotes_',
                'card_motivation_'
            ])
        }
        
        self.stdout.write(f"Found {len(motivational_paths)} motivational card paths")
        
        if opts["dry_run"]:
            self.stdout.write("DRY RUN - Would import:")
            for path in sorted(motivational_paths):
                self.stdout.write(f"  {path}")
            return
        
        # Import/activate cards
        created = 0
        reactivated = 0
        skipped = 0
        
        for path in motivational_paths:
            try:
                obj, was_created = MotivationalCard.objects.get_or_create(
                    path=path, 
                    defaults={
                        "is_active": True,
                        "title": "Motivational Card",
                        "message": "Stay motivated!",
                        "category": "quotes" if "quotes" in path else "motivation"
                    }
                )
                
                if was_created:
                    created += 1
                elif not obj.is_active:
                    obj.is_active = True
                    obj.save(update_fields=["is_active"])
                    reactivated += 1
                else:
                    skipped += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to import {path}: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete: {created} created, {reactivated} reactivated, "
                f"{skipped} skipped, {len(motivational_paths)} total"
            )
        )
        
        # Deactivate missing cards if requested
        if opts["deactivate_missing"]:
            deactivated = MotivationalCard.objects.exclude(
                path__in=motivational_paths
            ).update(is_active=False)
            self.stdout.write(f"Deactivated {deactivated} missing cards")
        
        # Show final stats
        active_count = MotivationalCard.objects.filter(is_active=True).count()
        total_count = MotivationalCard.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Final state: {active_count} active cards out of {total_count} total"
            )
        )

    def _load_from_r2_state(self):
        """Load paths from r2_upload_state.json"""
        try:
            r2_state_path = os.path.join(settings.BASE_DIR, 'r2_upload_state.json')
            if not os.path.exists(r2_state_path):
                self.stdout.write(
                    self.style.WARNING(f"R2 state file not found: {r2_state_path}")
                )
                return set()
                
            with open(r2_state_path, 'r', encoding='utf-8') as f:
                uploaded_files = json.load(f)
                
            if isinstance(uploaded_files, list):
                return set(uploaded_files)
            elif isinstance(uploaded_files, dict):
                # If it's a dict, extract all string values that look like paths
                paths = set()
                for value in uploaded_files.values():
                    if isinstance(value, str) and '/' in value:
                        paths.add(value)
                return paths
            else:
                self.stdout.write(
                    self.style.WARNING(f"Unexpected R2 state format: {type(uploaded_files)}")
                )
                return set()
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to load R2 state: {e}")
            )
            return set()

    def _load_from_file(self, file_path):
        """Load paths from text file (one path per line)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                paths = {line.strip() for line in f if line.strip()}
            return paths
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to load from file {file_path}: {e}")
            )
            return set()