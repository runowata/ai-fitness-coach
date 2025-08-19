from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction

SAFE_FIXTURES = [
    "stories.json",
    "achievements.json",
    "motivational_cards.json",
]

class Command(BaseCommand):
    help = "Load core fixtures idempotently; skips on-existing pk conflicts"

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            for fx in SAFE_FIXTURES:
                self.stdout.write(self.style.MIGRATE_HEADING(f"-> {fx}"))
                call_command("loaddata", f"fixtures/{fx}", verbosity=1)
        self.stdout.write(self.style.SUCCESS("Seed complete"))