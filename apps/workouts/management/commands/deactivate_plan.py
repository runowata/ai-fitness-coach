"""Management command to deactivate a workout plan"""
from django.core.management.base import BaseCommand
from apps.workouts.models import WorkoutPlan


class Command(BaseCommand):
    help = 'Deactivate a workout plan by ID'

    def add_arguments(self, parser):
        parser.add_argument('plan_id', type=int, help='ID of the plan to deactivate')

    def handle(self, *args, **options):
        plan_id = options['plan_id']

        try:
            plan = WorkoutPlan.objects.get(id=plan_id)

            self.stdout.write(f"Plan: {plan.name}")
            self.stdout.write(f"User: {plan.user.email}")
            self.stdout.write(f"Status: {plan.status}")
            self.stdout.write(f"Active: {plan.is_active}")

            plan.is_active = False
            plan.save()

            self.stdout.write(self.style.SUCCESS(f'Successfully deactivated plan {plan_id}'))

        except WorkoutPlan.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Plan {plan_id} does not exist'))
