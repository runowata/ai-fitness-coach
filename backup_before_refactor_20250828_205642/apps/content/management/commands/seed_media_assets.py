import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.content.models import MediaAsset

User = get_user_model()

AVATAR = "avatar"
CARD_BG = "card_background"

ASSET_TYPE_IMAGE = "image"
CDN_READY = "ready"


class Command(BaseCommand):
    help = "Seed minimal media assets (avatars + card backgrounds) from Cloudflare R2"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Don't write to DB, only print what would be created/updated",
        )
        parser.add_argument(
            "--force-reseed",
            action="store_true",
            help="Recreate records for the same (category, archetype, file_name)",
        )

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        force = opts["force_reseed"]

        # For R2 with signed URLs, we store R2 keys for MediaService to handle
        self.stdout.write("Using R2 storage with signed URL support")

        # These R2 keys should match actual files in your bucket
        avatar_keys = {
            "peer": "images/avatars/peer_avatar_1.jpg",
            "professional": "images/avatars/professional_avatar_1.jpg", 
            "mentor": "images/avatars/mentor_avatar_1.jpg",
        }

        card_bg_keys = [
            "images/cards/card_motivation_1.jpg",
            "images/cards/card_motivation_2.jpg", 
            "images/cards/card_motivation_3.jpg",
        ]

        # For R2, we'll store a placeholder URL and let MediaService generate signed URLs
        # The actual R2 key will be stored for reference
        placeholder_url = "r2://placeholder"  # Special marker for R2 files

        plan = []
        # 1) Avatars per archetype
        for archetype, key in avatar_keys.items():
            plan.append(
                dict(
                    file_name=os.path.basename(key),
                    file_url=f"r2://{key}",  # Store R2 key for MediaService
                    file_size=0,  # unknown - ok
                    asset_type=ASSET_TYPE_IMAGE,
                    category=AVATAR,
                    tags=[archetype, "avatar"],
                    archetype=archetype,  # 'peer' | 'professional' | 'mentor'
                    duration_seconds=None,
                    width=None,
                    height=None,
                    is_active=True,
                    cdn_url=placeholder_url,  # Will be generated dynamically
                    cdn_status=CDN_READY,
                    exercise=None,
                    uploaded_by=None,
                )
            )

        # 2) Card backgrounds (no archetype binding)
        for key in card_bg_keys:
            plan.append(
                dict(
                    file_name=os.path.basename(key),
                    file_url=f"r2://{key}",  # Store R2 key for MediaService
                    file_size=0,
                    asset_type=ASSET_TYPE_IMAGE,
                    category=CARD_BG,
                    tags=["card", "background"],
                    archetype="",  # empty - universal
                    duration_seconds=None,
                    width=None,
                    height=None,
                    is_active=True,
                    cdn_url=placeholder_url,  # Will be generated dynamically
                    cdn_status=CDN_READY,
                    exercise=None,
                    uploaded_by=None,
                )
            )

        self.stdout.write(self.style.MIGRATE_HEADING("Seeding media assets..."))
        self.stdout.write(f"R2 storage mode: files will use signed URLs")
        self.stdout.write(f"Planned records: {len(plan)}")
        if dry:
            self.stdout.write(self.style.WARNING("DRY RUN — no DB writes"))

        created, updated, skipped, replaced = 0, 0, 0, 0

        # Conditional "uniqueness": (category, archetype, file_name)
        # If force-reseed - delete existing and create new.
        with transaction.atomic():
            for item in plan:
                q = MediaAsset.objects.filter(
                    category=item["category"],
                    archetype=item["archetype"],
                    file_name=item["file_name"],
                )
                exists = q.first()

                if exists and not force:
                    # Update URL/status in case of CDN change
                    changed = False
                    for field in ("file_url", "cdn_url", "cdn_status", "is_active"):
                        if getattr(exists, field) != item[field]:
                            setattr(exists, field, item[field])
                            changed = True
                    if changed:
                        if not dry:
                            exists.save(update_fields=["file_url", "cdn_url", "cdn_status", "is_active"])
                        updated += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Updated: {item['category']} {item['archetype']} {item['file_name']}"
                            )
                        )
                    else:
                        skipped += 1
                        self.stdout.write(
                            f"Skip (exists): {item['category']} {item['archetype']} {item['file_name']}"
                        )
                    continue

                if exists and force:
                    replaced += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"Force re-seed: delete existing {item['category']} {item['archetype']} {item['file_name']}"
                        )
                    )
                    if not dry:
                        exists.delete()

                if not dry:
                    MediaAsset.objects.create(**item)
                created += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created: {item['category']} {item['archetype']} {item['file_name']}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Done"))
        self.stdout.write(
            f"Created: {created}, Updated: {updated}, Replaced: {replaced}, Skipped: {skipped}"
        )