from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction

SAFE_FIXTURES = [
    "exercises.json",
    "onboarding_questions.json", 
    "motivational_cards.json",
    "stories.json",
    "achievements.json",
]

class Command(BaseCommand):
    help = "Load core fixtures safely (idempotent); skips broken fixtures"

    def handle(self, *args, **kwargs):
        loaded = 0
        errors = 0
        
        for fx in SAFE_FIXTURES:
            self.stdout.write(self.style.MIGRATE_HEADING(f"-> {fx}"))
            try:
                call_command("loaddata", f"fixtures/{fx}", verbosity=1)
                loaded += 1
            except Exception as e:
                self.stderr.write(self.style.WARNING(f"Skipping {fx}: {e}"))
                errors += 1
        
        if errors > 0:
            self.stdout.write(self.style.WARNING(f"Loaded {loaded} fixtures, {errors} failed"))
        else:
            self.stdout.write(self.style.SUCCESS(f"All {loaded} fixtures loaded successfully"))