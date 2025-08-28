from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from apps.workouts.models import WorkoutPlan, DailyWorkout
from apps.workouts.services.playlist_builder import R2PlaylistBuilder

User = get_user_model()

class Command(BaseCommand):
    help = "Строит плейлисты для всех дней активного плана пользователя (без ИИ)."

    def add_arguments(self, parser):
        parser.add_argument("user_id", type=int, help="ID пользователя")
        parser.add_argument(
            "--archetype",
            type=str,
            help="Архетип тренера (peer, professional, mentor)"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только показать что будет сделано"
        )

    def handle(self, *args, **opts):
        user_id = opts["user_id"]
        archetype = opts.get("archetype")
        dry_run = opts.get("dry_run", False)
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise CommandError(f"User {user_id} not found")

        # Определяем архетип из профиля если не задан
        if not archetype and hasattr(user, 'profile'):
            archetype = user.profile.archetype_name
            
        self.stdout.write(f"User: {user.email}")
        self.stdout.write(f"Archetype: {archetype or 'universal'}")

        plan = WorkoutPlan.objects.filter(user=user, status="CONFIRMED").first()
        if not plan:
            raise CommandError("No confirmed plan found. Создайте демо-план сначала.")

        self.stdout.write(f"Plan: {plan.name}")

        # Получаем только тренировочные дни (не дни отдыха)
        days = DailyWorkout.objects.filter(
            plan=plan, 
            is_rest_day=False
        ).order_by("week_number", "day_number")
        
        if not days:
            self.stdout.write(self.style.WARNING("No training days found in plan"))
            return

        self.stdout.write(f"Found {days.count()} training days")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - no changes will be made"))

        total_items = 0
        for day in days:
            if dry_run:
                self.stdout.write(f"Would build playlist for Day {day.day_number}: {day.name}")
                continue
                
            builder = R2PlaylistBuilder(day, archetype)
            built = builder.build()
            summary = builder.get_playlist_summary()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Day {day.day_number}: built {built} items "
                    f"({', '.join(f'{role}: {count}' for role, count in summary['by_role'].items())})"
                )
            )
            total_items += built

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"Done. Total playlist items created: {total_items}")
            )
        else:
            self.stdout.write("DRY RUN completed - no database changes made")