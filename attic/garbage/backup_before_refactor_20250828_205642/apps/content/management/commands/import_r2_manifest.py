import json
import os
from django.core.management.base import BaseCommand, CommandError
from apps.content.models import MediaAsset

ASSET_TYPE_VIDEO = "video"

class Command(BaseCommand):
    help = "Импортирует R2 медиа по локальному manifest.json (категория -> список ключей)."

    def add_arguments(self, parser):
        parser.add_argument("manifest_path", type=str, help="Путь к JSON манифесту")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только показать что будет импортировано"
        )

    def handle(self, *args, **opts):
        path = opts["manifest_path"]
        dry_run = opts.get("dry_run", False)
        
        if not os.path.exists(path):
            raise CommandError(f"Manifest not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.stdout.write(f"Loading manifest from: {path}")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - no database changes"))

        created = updated = 0
        for category, keys in data.items():
            self.stdout.write(f"\nCategory: {category} ({len(keys)} files)")
            for key in keys:
                defaults = dict(
                    file_name=os.path.basename(key),
                    file_url=f"r2://{key}",
                    file_size=0,
                    asset_type=ASSET_TYPE_VIDEO,
                    category=category,
                    tags=[],
                    archetype="",
                    duration_seconds=None,
                    width=None, 
                    height=None,
                    is_active=True,
                    cdn_url="r2://placeholder",
                    cdn_status="ready",
                    exercise=None,
                    uploaded_by=None,
                )
                
                if dry_run:
                    self.stdout.write(f"  Would import: {category} {key}")
                    continue
                
                obj, is_created = MediaAsset.objects.update_or_create(
                    category=category, 
                    file_url=defaults["file_url"], 
                    defaults=defaults
                )
                
                created += int(is_created)
                updated += int(not is_created)
                action = "Created" if is_created else "Updated"
                self.stdout.write(f"  {action}: {category} {key}")

        self.stdout.write(
            self.style.SUCCESS(f"\nDone. Created: {created}, Updated: {updated}")
        )