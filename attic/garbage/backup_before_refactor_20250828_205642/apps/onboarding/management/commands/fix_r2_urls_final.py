from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.functions import Replace
from django.db.models import Value
from apps.onboarding.models import MotivationalCard


class Command(BaseCommand):
    help = "Replace old R2 public base URLs in MotivationalCard fields (image_url). Supports dry-run mode."

    def add_arguments(self, parser):
        parser.add_argument(
            "--old", 
            required=True, 
            help="Old base URL, e.g. https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev/"
        )
        parser.add_argument(
            "--new", 
            required=True, 
            help="New base URL, e.g. https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev/"
        )
        parser.add_argument(
            "--dry-run", 
            action="store_true", 
            help="Preview changes only, do not apply them"
        )

    def handle(self, *args, **options):
        old_base = options["old"].rstrip("/") + "/"
        new_base = options["new"].rstrip("/") + "/"
        dry_run = options["dry_run"]

        # Find records to update
        image_url_qs = MotivationalCard.objects.filter(image_url__startswith=old_base)
        
        self.stdout.write(f"Old base: {old_base}")
        self.stdout.write(f"New base: {new_base}")
        self.stdout.write("-" * 60)
        self.stdout.write(f"Found MotivationalCard.image_url records to replace: {image_url_qs.count()}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN MODE: No changes will be applied."))
            
            # Show sample records that would be changed
            sample_records = list(image_url_qs.values('id', 'image_url')[:5])
            if sample_records:
                self.stdout.write("\nSample records that would be updated:")
                for record in sample_records:
                    old_url = record['image_url']
                    new_url = old_url.replace(old_base, new_base, 1)
                    self.stdout.write(f"  ID {record['id']}:")
                    self.stdout.write(f"    Before: {old_url}")
                    self.stdout.write(f"    After:  {new_url}")
            else:
                self.stdout.write("No records found to update.")
            return

        # Apply changes
        if image_url_qs.count() == 0:
            self.stdout.write(self.style.WARNING("No records found to update."))
            return

        with transaction.atomic():
            updated_count = image_url_qs.update(
                image_url=Replace("image_url", Value(old_base), Value(new_base))
            )
            
            self.stdout.write(
                self.style.SUCCESS(f"Successfully updated {updated_count} MotivationalCard.image_url records")
            )

        # Verify updates
        remaining_count = MotivationalCard.objects.filter(image_url__startswith=old_base).count()
        if remaining_count == 0:
            self.stdout.write(self.style.SUCCESS("✓ All old URLs have been successfully replaced"))
        else:
            self.stdout.write(
                self.style.WARNING(f"⚠ Warning: {remaining_count} records still contain old URLs")
            )