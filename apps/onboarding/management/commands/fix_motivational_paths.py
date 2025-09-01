"""
Management command to fix motivational card paths in production.

This fixes paths that are missing the 'photos/' prefix.
"""

from django.core.management.base import BaseCommand
from apps.onboarding.models import MotivationalCard


class Command(BaseCommand):
    help = 'Fix motivational card paths by adding photos/ prefix if missing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("🔍 Checking motivational card paths...")
        
        # Find cards with paths that need fixing
        cards = MotivationalCard.objects.filter(
            is_active=True,
            path__isnull=False
        ).exclude(path='')
        
        cards_to_fix = []
        for card in cards:
            if card.path and not card.path.startswith('photos/'):
                cards_to_fix.append(card)
        
        self.stdout.write(f"Found {len(cards_to_fix)} cards that need path fixes")
        
        if not cards_to_fix:
            self.stdout.write(self.style.SUCCESS("✅ All paths are already correct!"))
            return
        
        # Show what will be changed
        for card in cards_to_fix:
            old_path = card.path
            new_path = f"photos/{old_path}" if not old_path.startswith('photos/') else old_path
            
            self.stdout.write(f"Card {card.id}:")
            self.stdout.write(f"  OLD: {old_path}")
            self.stdout.write(f"  NEW: {new_path}")
            self.stdout.write(f"  URL: https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev/{new_path}")
            self.stdout.write("")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN - No changes made"))
            return
        
        # Ask for confirmation
        confirm = input(f"Fix {len(cards_to_fix)} card paths? (y/N): ")
        if confirm.lower() != 'y':
            self.stdout.write("❌ Cancelled")
            return
        
        # Apply fixes
        fixed_count = 0
        for card in cards_to_fix:
            old_path = card.path
            if not old_path.startswith('photos/'):
                card.path = f"photos/{old_path}"
                card.save()
                fixed_count += 1
                self.stdout.write(f"✅ Fixed card {card.id}: {old_path} -> {card.path}")
        
        self.stdout.write(self.style.SUCCESS(f"🎉 Fixed {fixed_count} motivational card paths!"))
        
        # Test a few URLs
        self.stdout.write("\n🧪 Testing fixed URLs...")
        test_cards = cards_to_fix[:3]
        
        import requests
        for card in test_cards:
            url = f"https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev/{card.path}"
            try:
                response = requests.head(url, timeout=5)
                status = "✅ OK" if response.status_code == 200 else f"❌ {response.status_code}"
                self.stdout.write(f"{status} {url}")
            except Exception as e:
                self.stdout.write(f"❌ ERROR {url}: {e}")
        
        self.stdout.write(self.style.SUCCESS("\n🚀 All done! Motivational cards should now display properly."))