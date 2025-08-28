"""
Management command to update R2 URLs to the correct domain
"""
import os

from django.core.management.base import BaseCommand

from apps.onboarding.models import MotivationalCard


class Command(BaseCommand):
    help = 'Update R2 URLs to use the correct domain from environment'
    
    def handle(self, *args, **options):
        # Get correct domain from environment
        r2_public_base = os.getenv('R2_PUBLIC_BASE', '')
        if not r2_public_base:
            # Fallback to construct from bucket name
            r2_bucket = os.getenv('R2_BUCKET', '')
            if r2_bucket:
                r2_public_base = "https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev"
            else:
                self.stdout.write(self.style.ERROR('Neither R2_PUBLIC_BASE nor R2_BUCKET set in environment'))
                return
            
        self.stdout.write(f"Using R2 public base: {r2_public_base}")
        
        # Old domain patterns to replace
        old_domains = [
            'https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev',
            'https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev',  # In case there are mixed
        ]
        
        # Update motivational cards
        updated_count = 0
        cards = MotivationalCard.objects.all()
        
        for card in cards:
            if card.image_url:
                for old_domain in old_domains:
                    if old_domain in card.image_url:
                        # Extract path after domain
                        path = card.image_url.replace(old_domain, '')
                        # Build new URL
                        card.image_url = f"{r2_public_base}{path}"
                        card.save(update_fields=['image_url'])
                        updated_count += 1
                        self.stdout.write(f"Updated card {card.id}: {card.image_url}")
                        break
                        
        self.stdout.write(self.style.SUCCESS(f"Updated {updated_count} motivational cards"))