from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils import timezone
from rest_framework import generics, permissions
from .forms import UserRegistrationForm, UserProfileForm
from .models import User, UserProfile
from .serializers import ArchetypeSerializer


class RegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('onboarding:start')
    
    def form_valid(self, form):
        # Verify age confirmation
        if not form.cleaned_data.get('age_confirmed'):
            messages.error(self.request, 'Вы должны подтвердить, что вам 18 лет или больше.')
            return self.form_invalid(form)
        
        # Create user
        response = super().form_valid(form)
        
        # Create profile if it doesn't exist
        UserProfile.objects.get_or_create(user=self.object)
        
        # Auto-login
        user = authenticate(
            username=self.object.username,
            password=form.cleaned_data['password1']
        )
        if user:
            login(self.request, user)
        else:
            # If authentication fails, login with the created user directly
            login(self.request, self.object)
        
        messages.success(self.request, 'Добро пожаловать! Давайте создадим вашу персональную программу.')
        return response


@login_required
def dashboard_view(request):
    """Main dashboard showing today's workout"""
    user = request.user
    
    # Get or create user profile if it doesn't exist
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
        messages.info(request, 'Создан профиль пользователя. Пройдите онбординг для настройки!')
    
    # Get active workout plan
    workout_plan = user.workout_plans.filter(is_active=True).first()
    
    if not workout_plan:
        messages.info(request, 'У вас пока нет активного плана тренировок. Пройдите онбординг!')
        return redirect('onboarding:start')
    
    # CRITICAL FIX: Set started_at if it's missing (for old plans)
    if not workout_plan.started_at:
        workout_plan.started_at = timezone.now()
        workout_plan.save()
    
    # Get today's workout
    current_week = workout_plan.get_current_week()
    days_since_start = (timezone.now() - workout_plan.started_at).days if workout_plan.started_at else 0
    current_day = (days_since_start % 7) + 1
    
    today_workout = workout_plan.daily_workouts.filter(
        week_number=current_week,
        day_number=current_day
    ).first()
    
    # Check achievements
    from apps.achievements.services import AchievementChecker
    checker = AchievementChecker()
    new_achievements = checker.check_user_achievements(user)
    
    context = {
        'profile': profile,
        'workout_plan': workout_plan,
        'today_workout': today_workout,
        'current_week': current_week,
        'new_achievements': new_achievements,
        'streak': profile.current_streak,
        'xp': profile.experience_points,
        'level': profile.level,
    }
    
    return render(request, 'users/dashboard.html', context)


@login_required
def profile_settings_view(request):
    """User profile settings"""
    profile = request.user.profile
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Настройки сохранены!')
            return redirect('users:dashboard')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'users/profile_settings.html', {'form': form})


class ArchetypeView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ArchetypeSerializer
    
    def get_object(self):
        return self.request.user.profile