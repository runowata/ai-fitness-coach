"""
Management command to load onboarding data (questions, options, cards)
"""
import os
import random
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.management import call_command
from apps.onboarding.models import MotivationalCard


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
        
        # Base R2 URL for card images
        base_url = "https://pub-9b30caf23edc4d0b8509a7fb15c2bd5a.r2.dev/photos/progress"
        
        # Available card images (we know these exist)
        image_numbers = [
            "0023", "0024", "0025", "0037", "0042", "0054", "0066", "0072", "0073",
            "0094", "0097", "0099", "0102", "0103", "0104", "0106", "0112", "0122",
            "0135", "0137", "0142", "0143", "0144", "0170", "0180", "0182", "0189",
            "0199", "0208", "0217", "0235", "0245", "0255", "0258", "0259", "0270",
            "0275", "0304", "0310", "0332", "0338", "0343", "0345", "0347", "0350",
            "0353", "0354", "0366", "0374", "0390", "0396", "0427", "0448", "0449",
            "0455", "0460", "0461", "0462", "0468", "0469", "0476", "0477", "0488",
            "0489"
        ]
        
        # Get all motivational cards
        cards = MotivationalCard.objects.filter(is_active=True, image_url='')
        
        for card in cards:
            # Pick random image number
            image_num = random.choice(image_numbers)
            image_url = f"{base_url}/card_progress_{image_num}.jpg"
            
            card.image_url = image_url
            card.save()
            
            self.stdout.write(f"Card {card.id}: assigned card_progress_{image_num}.jpg")
        
        self.stdout.write(f"Added images to {cards.count()} cards")