from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.management import call_command
from apps.onboarding.models import OnboardingSession, UserOnboardingResponse
from apps.achievements.models import Achievement, UserAchievement, XPTransaction
from apps.workouts.models import DailyWorkout, WorkoutPlan

class Command(BaseCommand):
    help = "Create demo user + seed minimal product path"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        user, _ = User.objects.get_or_create(
            email="demo@example.com",
            defaults={"username":"demo","is_active":True}
        )
        user.set_password("demo12345")
        user.save()

        # базовые фикстуры (идемпотентно)
        call_command("seed_safe")

        # онбординг (минимальный валидный сет ответов)
        session, _ = OnboardingSession.objects.get_or_create(user=user)
        from apps.onboarding.models import OnboardingQuestion
        question = OnboardingQuestion.objects.first()
        if question:
            UserOnboardingResponse.objects.get_or_create(
                user=user, question=question, defaults={"answer_text":"demo"}
            )

        # тренировочный план на 7 дней
        plan, _ = WorkoutPlan.objects.get_or_create(user=user, defaults={"plan_data":{}})
        for i in range(7):
            DailyWorkout.objects.get_or_create(
                plan=plan,
                day_number=i+1,
                defaults={"name":f"Day {i+1}", "exercises":[], "week_number":1}
            )

        # ачивки и XP
        ach = Achievement.objects.first()
        if ach:
            UserAchievement.objects.get_or_create(user=user, achievement=ach)
            XPTransaction.objects.get_or_create(
                user=user, amount=10, transaction_type="daily_login", 
                defaults={"description": "Bootstrap demo", "created_at": timezone.now()}
            )
        self.stdout.write(self.style.SUCCESS("Demo bootstrap complete"))