from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.workouts.models import WorkoutPlan

User = get_user_model()

class Command(BaseCommand):
    help = 'Reset onboarding status for all users and deactivate their workout plans'

    def handle(self, *args, **options):
        # Reset all users' onboarding status
        user_count = User.objects.count()
        User.objects.update(
            onboarding_completed_at=None,
            archetype='',
        )
        
        # Deactivate all workout plans
        plan_count = WorkoutPlan.objects.filter(is_active=True).count()
        WorkoutPlan.objects.filter(is_active=True).update(is_active=False)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully reset onboarding for {user_count} users '
                f'and deactivated {plan_count} workout plans'
            )
        )