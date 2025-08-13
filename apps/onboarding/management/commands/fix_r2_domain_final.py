"""
Management command to fix motivational card URLs to correct R2 domain
From Cloudflare Dashboard we see the actual domain is:
https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev
"""
from django.core.management.base import BaseCommand

from apps.onboarding.models import MotivationalCard


class Command(BaseCommand):
    help = 'Fix motivational card URLs to use actual R2 Public Development URL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        self.stdout.write("Fixing motivational card URLs to actual R2 domain...")
        
        # Actual domain from Cloudflare Dashboard
        correct_domain = "https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev"
        
        # Old domains we need to replace
        old_domains = [
            "https://pub-9b30caf23edc4d0b8509a7fb15c2bd5a.r2.dev",
            "https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev"
        ]
        
        # Find cards that need updating
        cards_to_fix = MotivationalCard.objects.filter(
            image_url__regex=r'https://pub-[a-z0-9]+\.r2\.dev/photos/progress/'
        ).exclude(
            image_url__startswith=correct_domain
        )
        
        self.stdout.write(f"Found {cards_to_fix.count()} cards with incorrect domain URLs")
        
        if options['dry_run']:
            self.stdout.write("DRY RUN - showing what would be changed:")
            
        updated_count = 0
        for card in cards_to_fix:
            old_url = card.image_url
            
            # Replace any old domain with correct one
            new_url = old_url
            for old_domain in old_domains:
                if old_domain in old_url:
                    new_url = old_url.replace(old_domain, correct_domain)
                    break
            
            if new_url == old_url:
                # Fallback: replace any pub-*.r2.dev domain
                import re
                new_url = re.sub(
                    r'https://pub-[a-z0-9]+\.r2\.dev',
                    correct_domain,
                    old_url
                )
            
            if options['dry_run']:
                self.stdout.write(f"Card {card.id}:")
                self.stdout.write(f"  OLD: {old_url}")
                self.stdout.write(f"  NEW: {new_url}")
            else:
                card.image_url = new_url
                card.save()
                filename = new_url.split('/')[-1]
                self.stdout.write(f"Updated card {card.id}: {filename}")
                updated_count += 1
        
        if not options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {updated_count} motivational card URLs')
            )
            self.stdout.write(f"Now using correct domain: {correct_domain}")
        else:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would update {cards_to_fix.count()} URLs')
            )