import random
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from apps.workouts.models import WorkoutPlan, DailyWorkout

User = get_user_model()

BASIC_EXERCISES = [
    {"slug": "pushups", "name": "Отжимания"},
    {"slug": "squats", "name": "Приседания"},
    {"slug": "plank", "name": "Планка"},
    {"slug": "burpee", "name": "Берпи"},
]

class Command(BaseCommand):
    help = "Создаёт демо-план без таблицы Exercise (только JSON в DailyWorkout)."
    def add_arguments(self, parser): parser.add_argument("user_id", type=int)

    def handle(self, *args, **opts):
        user_id = opts["user_id"]
        try: user = User.objects.get(pk=user_id)
        except User.DoesNotExist: raise CommandError(f"Пользователь id={user_id} не найден")
        self.stdout.write(f"✅ Пользователь: {getattr(user,'email',user.username)}")

        plan = WorkoutPlan.objects.filter(user=user, status="CONFIRMED").first()
        if not plan:
            plan = WorkoutPlan.objects.create(
                user=user, name="Демо-план на 1 неделю", duration_weeks=4,
                plan_data={"demo": True, "source": "create_demo_plan"}, status="CONFIRMED",
            )
            self.stdout.write(self.style.SUCCESS(f"📅 Создан план: {plan.name} (id={plan.id})"))
        else:
            DailyWorkout.objects.filter(plan=plan).delete()
            self.stdout.write("♻️ Пересоздаю дни в существующем плане")

        for day in range(1, 8):
            is_rest = day in (3, 6)
            if is_rest:
                exercises = []; name = "День отдыха"
            else:
                # Защита от случая когда упражнений меньше 3
                exercise_count = min(3, len(BASIC_EXERCISES))
                chosen = random.sample(BASIC_EXERCISES, k=exercise_count) if BASIC_EXERCISES else []
                exercises = [
                    {"exercise_id": e["slug"], "exercise_name": e["name"],
                     "sets": 3, "reps": random.randint(8,15), "rest_seconds": 60}
                    for e in chosen
                ]
                name = f"Тренировка день {day}"

            dw = DailyWorkout.objects.create(
                plan=plan, day_number=day, week_number=1,
                name=name, exercises=exercises, is_rest_day=is_rest,
            )
            self.stdout.write(f"   День {day}: {'отдых' if is_rest else ', '.join(x['exercise_name'] for x in exercises)} (dw_id={dw.id})")

        self.stdout.write(self.style.SUCCESS("🎉 Демо-план готов."))