"""
Management command to fix motivational card URLs from old to new R2 domain
"""
from django.core.management.base import BaseCommand
from apps.onboarding.models import MotivationalCard


class Command(BaseCommand):
    help = 'Fix motivational card URLs to use correct R2 domain'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        self.stdout.write("Fixing motivational card URLs...")
        
        # Old and new domains
        old_domain = "https://pub-9b30caf23edc4d0b8509a7fb15c2bd5a.r2.dev"
        new_domain = "https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev"
        
        # Find cards with old domain
        cards_to_fix = MotivationalCard.objects.filter(
            image_url__startswith=old_domain
        )
        
        self.stdout.write(f"Found {cards_to_fix.count()} cards with old domain URLs")
        
        if options['dry_run']:
            self.stdout.write("DRY RUN - showing what would be changed:")
            
        updated_count = 0
        for card in cards_to_fix:
            old_url = card.image_url
            new_url = card.image_url.replace(old_domain, new_domain)
            
            if options['dry_run']:
                self.stdout.write(f"Card {card.id}:")
                self.stdout.write(f"  OLD: {old_url}")
                self.stdout.write(f"  NEW: {new_url}")
            else:
                card.image_url = new_url
                card.save()
                self.stdout.write(f"Updated card {card.id}: {new_url.split('/')[-1]}")
                updated_count += 1
        
        if not options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {updated_count} motivational card URLs')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would update {cards_to_fix.count()} URLs')
            )