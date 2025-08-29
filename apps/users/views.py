from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView
from rest_framework import generics, permissions

from .forms import UserProfileForm, UserRegistrationForm
from .models import User, UserProfile
from .serializers import ArchetypeSerializer, UserSerializer


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
    
    # Safe guard: Get or create user profile
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    # Get active workout plan with safe handling
    workout_plan = user.workout_plans.filter(is_active=True).first()
    
    # Safe variables for template
    today_workout = None
    current_week = 1
    new_achievements = []
    
    if workout_plan:
        try:
            # CRITICAL FIX: Set started_at if it's missing (for old plans)
            if not workout_plan.started_at:
                workout_plan.started_at = timezone.now()
                workout_plan.save()
            
            # Get today's workout with error handling
            current_week = workout_plan.get_current_week()
            days_since_start = (timezone.now() - workout_plan.started_at).days if workout_plan.started_at else 0
            current_day = (days_since_start % 7) + 1
            
            today_workout = workout_plan.daily_workouts.filter(
                week_number=current_week,
                day_number=current_day
            ).first()
        except Exception as e:
            # Log error but don't crash
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error processing workout plan {workout_plan.id}: {e}")
            messages.warning(request, 'Есть проблемы с планом тренировок. Попробуйте обновить страницу.')
    
    # Achievements removed - no longer needed
    new_achievements = []
    
    # Safe context building
    context = {
        'profile': profile,
        'workout_plan': workout_plan,
        'today_workout': today_workout,
        'current_week': current_week,
        'new_achievements': new_achievements,
        'streak': getattr(profile, 'current_streak', 0),
        'xp': getattr(profile, 'experience_points', 0),
        'level': getattr(profile, 'level', 1),
    }
    
    return render(request, 'users/dashboard.html', context)


@login_required
def profile_settings_view(request):
    """User profile settings"""
    # Safe guard: Get or create user profile
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Настройки сохранены!')
            return redirect('users:dashboard')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'users/profile_settings.html', {'form': form})


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/profile/ - Get current user profile
    PATCH /api/profile/ - Update user profile  
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user


class ArchetypeView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ArchetypeSerializer
    
    def get_object(self):
        return self.request.user.profile