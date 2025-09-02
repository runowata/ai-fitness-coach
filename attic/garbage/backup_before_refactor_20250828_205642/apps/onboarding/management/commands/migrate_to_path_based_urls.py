from django.core.management.base import BaseCommand
from django.db import transaction
from apps.onboarding.models import MotivationalCard
import re


class Command(BaseCommand):
    help = "Complete migration from absolute URLs to path-based approach for MotivationalCard"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", 
            action="store_true", 
            help="Preview changes only, do not apply them"
        )
        parser.add_argument(
            "--clear-legacy-fields",
            action="store_true",
            help="Clear deprecated image_url field after migration (final step)"
        )

    def extract_path_from_url(self, url):
        """Extract relative path from R2 public URL"""
        if not url or not url.startswith('http'):
            return ''
        
        # Match pattern: https://pub-{hash}.r2.dev/{path}
        match = re.search(r'https://pub-[a-f0-9]+\.r2\.dev/(.+)', url)
        if match:
            return match.group(1)
        
        return ''

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        clear_legacy = options["clear_legacy_fields"]

        self.stdout.write("=== MotivationalCard Migration to Path-Based URLs ===")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN MODE: No changes will be applied"))
        
        # Step 1: Populate path field from image_url
        cards_without_path = MotivationalCard.objects.filter(
            image_url__isnull=False,
            path__in=['', None]
        ).exclude(image_url='')
        
        self.stdout.write(f"Cards needing path population: {cards_without_path.count()}")
        
        if cards_without_path.count() > 0:
            sample_cards = list(cards_without_path[:3].values('id', 'image_url'))
            for card in sample_cards:
                path = self.extract_path_from_url(card['image_url'])
                self.stdout.write(f"  ID {card['id']}: {card['image_url']} -> path: '{path}'")
            
            if not dry_run:
                with transaction.atomic():
                    updated_count = 0
                    for card in cards_without_path:
                        path = self.extract_path_from_url(card.image_url)
                        if path:
                            card.path = path
                            card.save(update_fields=['path'])
                            updated_count += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Populated path field for {updated_count} cards")
                    )
        
        # Step 2: Verify migration
        cards_with_path = MotivationalCard.objects.exclude(path__in=['', None]).count()
        cards_with_image_url = MotivationalCard.objects.exclude(image_url__in=['', None]).count()
        
        self.stdout.write(f"\nMigration status:")
        self.stdout.write(f"  Cards with path field: {cards_with_path}")
        self.stdout.write(f"  Cards with image_url field: {cards_with_image_url}")
        
        # Step 3: Clear legacy fields (optional)
        if clear_legacy and not dry_run:
            self.stdout.write("\nClearing legacy image_url fields...")
            
            with transaction.atomic():
                cleared_count = MotivationalCard.objects.exclude(path__in=['', None]).update(
                    image_url=''
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Cleared image_url field from {cleared_count} cards")
                )
        
        # Step 4: Final verification
        if not dry_run:
            self.stdout.write("\nFinal verification:")
            
            # Test a few URLs
            test_cards = list(MotivationalCard.objects.filter(
                is_active=True
            ).exclude(path__in=['', None])[:3])
            
            if test_cards:
                from apps.onboarding.utils import public_r2_url
                
                for card in test_cards:
                    public_url = public_r2_url(card.path)
                    self.stdout.write(f"  Card {card.id}: path='{card.path}' -> {public_url}")
            
            self.stdout.write(self.style.SUCCESS("\n✓ Migration completed successfully!"))
            self.stdout.write("Next steps for production:")
            self.stdout.write("1. Set R2_PUBLIC_BASE environment variable")
            self.stdout.write("2. Deploy and test image loading")
            self.stdout.write("3. Run with --clear-legacy-fields to clean up (optional)")
        else:
            self.stdout.write("\nTo apply changes, run without --dry-run")