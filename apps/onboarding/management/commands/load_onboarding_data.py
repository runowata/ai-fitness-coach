"""
Management command to load onboarding data (questions, options, cards)
"""
import random

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.onboarding.models import MotivationalCard
from apps.workouts.models import R2Image


class Command(BaseCommand):
    help = 'Load onboarding data (questions, options, cards) with images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-images',
            action='store_true',
            help='Skip adding images to motivational cards',
        )

    def handle(self, *args, **options):
        self.stdout.write("Loading onboarding data...")
        
        # Load fixtures in order
        self.stdout.write("Loading onboarding questions...")
        call_command('loaddata', 'fixtures/onboarding_questions.json')
        
        self.stdout.write("Loading answer options...")
        call_command('loaddata', 'fixtures/answer_options.json')
        
        self.stdout.write("Loading motivational cards...")
        call_command('loaddata', 'fixtures/motivational_cards.json')
        
        if not options['skip_images']:
            self.add_images_to_cards()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully loaded onboarding data')
        )

    def add_images_to_cards(self):
        """Add images from R2 to motivational cards"""
        
        self.stdout.write("Adding images to motivational cards...")
        
        # Get cards that need image paths
        cards = MotivationalCard.objects.filter(
            is_active=True
        ).filter(Q(path__isnull=True) | Q(path=''))
        
        if not cards.exists():
            self.stdout.write("No cards need image paths. Skipping.")
            return
        
        # Get available R2 images for motivational content
        images = list(
            R2Image.objects.filter(
                is_active=True,
                category__in=['motivation', 'quotes', 'progress']
            ).order_by('code').values_list('code', flat=True)
        )
        
        if not images:
            self.stdout.write("No R2 images found for motivational cards. Skipping.")
            return
        
        # Assign image paths to cards
        for idx, card in enumerate(cards):
            # Use round-robin to distribute images
            code = images[idx % len(images)]
            card.path = code  # R2Image code is the full path
            card.save(update_fields=['path'])
            
            self.stdout.write(f"Card {card.id}: assigned image {code}")
        
        self.stdout.write(f"Added images to {cards.count()} cards")