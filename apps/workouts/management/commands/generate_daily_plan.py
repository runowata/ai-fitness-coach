from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from apps.workouts.services.plan_generator import generate_week_plan

class Command(BaseCommand):
    help = "Generate a 7-day workout plan for a user"

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--overwrite", action="store_true")

    def handle(self, *args, **opts):
        User = get_user_model()
        email = opts["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f"User {email} not found")
        plan = generate_week_plan(user, overwrite=opts["overwrite"])
        self.stdout.write(self.style.SUCCESS(f"Plan ready: {plan.id} for {email}"))