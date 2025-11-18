"""
Management command to fix is_rest_day flags for workouts that have playlists
"""
from django.core.management.base import BaseCommand
from apps.workouts.models import DailyWorkout, DailyPlaylistItem


class Command(BaseCommand):
    help = 'Fix is_rest_day flags for workouts that have video playlists'

    def add_arguments(self, parser):
        parser.add_argument(
            '--plan-id',
            type=int,
            help='Fix specific plan ID only',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        plan_id = options.get('plan_id')
        dry_run = options.get('dry_run', False)

        # Build query
        workouts = DailyWorkout.objects.filter(is_rest_day=True)
        if plan_id:
            workouts = workouts.filter(plan_id=plan_id)

        # Find workouts that have playlists but marked as rest days
        fixed_count = 0
        for workout in workouts:
            playlist_count = workout.playlist_items.count()

            if playlist_count > 0:
                self.stdout.write(
                    f"Workout {workout.id} (Day {workout.day_number}, Week {workout.week_number}): "
                    f"{workout.name} - has {playlist_count} videos but marked as rest day"
                )

                if not dry_run:
                    workout.is_rest_day = False
                    workout.save(update_fields=['is_rest_day'])
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Fixed workout {workout.id}"))
                else:
                    self.stdout.write(self.style.WARNING(f"  → Would fix workout {workout.id} (dry-run)"))

                fixed_count += 1

        if fixed_count == 0:
            self.stdout.write(self.style.SUCCESS("No workouts need fixing!"))
        else:
            if dry_run:
                self.stdout.write(self.style.WARNING(f"\nWould fix {fixed_count} workouts (dry-run mode)"))
            else:
                self.stdout.write(self.style.SUCCESS(f"\n✓ Fixed {fixed_count} workouts"))
