from django.utils import timezone
from apps.workouts.models import WorkoutPlan, DailyWorkout, Exercise
from apps.users.models import UserProfile
import random

DEFAULT_EX_COUNT = 6

def generate_week_plan(user, *, name="Auto plan", overwrite=False):
    plan, created = WorkoutPlan.objects.get_or_create(user=user, defaults={"plan_data": {}, "name": name})
    if overwrite and not created:
        DailyWorkout.objects.filter(plan=plan).delete()
    # простая логика подбора: выбираем N упражнений случайно по тэгам уровня
    profile = UserProfile.objects.filter(user=user).first()
    level = (profile and profile.level) or "beginner"
    ex_qs = Exercise.objects.all()
    if level == "beginner":
        ex_qs = ex_qs.filter(difficulty__in=["easy","normal"])
    elif level == "advanced":
        ex_qs = ex_qs.exclude(difficulty="easy")
    ex_ids = list(ex_qs.values_list("exercise_slug", flat=True))
    for day in range(7):
        picks = random.sample(ex_ids, min(len(ex_ids), DEFAULT_EX_COUNT)) if ex_ids else []
        DailyWorkout.objects.get_or_create(
            plan=plan,
            day_number=day+1,
            defaults={
                "name": f"Day {day+1}",
                "exercises": picks,  # JSONField: список exercise_slug
                "week_number": 1,
            },
        )
    return plan