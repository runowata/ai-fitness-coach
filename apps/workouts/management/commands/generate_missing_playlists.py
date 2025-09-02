from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.workouts.models import WorkoutPlan, DailyWorkout, DailyPlaylistItem
from apps.workouts.services.playlist_generator_v2 import PlaylistGeneratorV2

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate playlists for workouts that are missing them'

    def add_arguments(self, parser):
        parser.add_argument('--plan-id', type=int, help='Generate only for specific plan ID')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        plan_id = options['plan_id']

        if plan_id:
            plans = WorkoutPlan.objects.filter(id=plan_id)
            if not plans.exists():
                self.stdout.write(self.style.ERROR(f'Plan {plan_id} not found'))
                return
        else:
            # Все планы со статусом CONFIRMED/ACTIVE
            plans = WorkoutPlan.objects.filter(status__in=['CONFIRMED', 'ACTIVE'])

        self.stdout.write(f'Found {plans.count()} plans to process')

        total_generated = 0
        
        for plan in plans:
            user = plan.user
            
            # Получаем архетип пользователя
            if hasattr(user, 'profile') and user.profile.archetype:
                archetype = user.profile.archetype
            else:
                archetype = 'mentor'
                
            self.stdout.write(f'\nPlan {plan.id} ({plan.name}) - User: {user.email} - Archetype: {archetype}')
            
            # Найдем тренировки без плейлистов
            workouts_without_playlists = []
            for workout in plan.daily_workouts.all():
                if workout.playlist_items.count() == 0:
                    workouts_without_playlists.append(workout)
            
            if not workouts_without_playlists:
                self.stdout.write('  ✅ All workouts already have playlists')
                continue
                
            self.stdout.write(f'  Found {len(workouts_without_playlists)} workouts without playlists')
            
            if dry_run:
                for workout in workouts_without_playlists:
                    self.stdout.write(f'    Would generate playlist for Day {workout.day_number}')
                continue
                
            # Генерируем плейлисты
            generator = PlaylistGeneratorV2(user, archetype)
            
            for workout in workouts_without_playlists:
                try:
                    items = generator.generate_playlist_for_day(workout.day_number, workout)
                    self.stdout.write(
                        self.style.SUCCESS(f'    ✅ Day {workout.day_number}: {len(items)} items generated')
                    )
                    total_generated += len(items)
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'    ❌ Day {workout.day_number}: Error - {e}')
                    )

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 Total playlist items generated: {total_generated}')
            )
        else:
            self.stdout.write('\n📋 Dry run completed - no changes made')