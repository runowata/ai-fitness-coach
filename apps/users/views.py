from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from .forms import UserRegistrationForm, UserSettingsForm
from .models import User


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
        
        # Create the user but don't save to DB yet
        user = form.save(commit=False)
        user.save()
        
        # Authenticate and login the user
        email = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password1')
        
        user = authenticate(request=self.request, email=email, password=password)
        
        if user is not None and user.is_active:
            login(self.request, user)
            messages.success(self.request, 'Добро пожаловать! Давайте создадим вашу персональную программу.')
            return redirect('onboarding:start')
        else:
            messages.error(self.request, 'Произошла ошибка при входе. Пожалуйста, войдите вручную.')
            return redirect('login')


@login_required
def dashboard_view(request):
    """Main dashboard showing today's workout"""
    user = request.user
    
    # Import here to avoid circular import
    from apps.onboarding.services import OnboardingService
    
    # Check if user needs to complete onboarding
    # Use validation method that can safely fix incorrect states
    if not OnboardingService.validate_and_fix_onboarding_status(user):
        return redirect('onboarding:start')
    
    # Use service to get dashboard context
    from .services import UserDashboardService
    context = UserDashboardService.get_dashboard_context(user)
    
    # Check for program completion message
    if context['program_completion_available']:
        messages.info(request, '🎉 Поздравляем! Вы завершили 6-недельную программу! Время выбрать новый цикл.')
    
    # Check if we created a default plan
    if not user.workout_plans.filter(is_active=True).exists():
        messages.success(request, 'Создан базовый план тренировок! Вы можете настроить его позже.')
    
    return render(request, 'users/dashboard.html', context)


@login_required
def profile_settings_view(request):
    """User profile settings"""
    user = request.user
    
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Настройки сохранены!')
            return redirect('users:dashboard')
    else:
        form = UserSettingsForm(instance=user)
    
    return render(request, 'users/profile_settings.html', {'form': form})


def debug_auth(request):
    """Debug view to check authentication status"""
    info = []
    info.append("<h2>DEBUG AUTHENTICATION STATUS</h2>")
    info.append(f"<b>User authenticated:</b> {request.user.is_authenticated}")
    info.append(f"<b>User:</b> {request.user}")
    info.append(f"<b>User ID:</b> {request.user.id if request.user.is_authenticated else 'N/A'}")
    info.append(f"<b>User type:</b> {type(request.user)}")
    info.append(f"<b>Session key:</b> {request.session.session_key}")
    info.append(f"<b>Session items:</b> {dict(request.session.items())}")
    
    # Check if user has onboarding completed
    if request.user.is_authenticated:
        info.append("<h3>USER DETAILS</h3>")
        info.append(f"<b>Email:</b> {request.user.email}")
        info.append(f"<b>Username:</b> {request.user.username}")
        info.append(f"<b>Is active:</b> {request.user.is_active}")
        info.append(f"<b>Is staff:</b> {request.user.is_staff}")
        info.append(f"<b>Date joined:</b> {request.user.date_joined}")
        info.append(f"<b>Last login:</b> {request.user.last_login}")
        info.append(f"<b>Onboarding completed:</b> {request.user.onboarding_completed_at}")
        info.append(f"<b>Archetype:</b> {getattr(request.user, 'archetype', 'None')}")
        
        # Check onboarding questions
        from apps.onboarding.models import OnboardingQuestion
        questions_count = OnboardingQuestion.objects.filter(is_active=True).count()
        info.append(f"<b>Active onboarding questions:</b> {questions_count}")
        
        # Check workout plans
        workout_plans = request.user.workout_plans.filter(is_active=True)
        info.append(f"<b>Active workout plans:</b> {workout_plans.count()}")
        
        # Check user responses
        responses_count = request.user.onboarding_responses.count()
        info.append(f"<b>Onboarding responses:</b> {responses_count}")
    
    # Check cookies
    info.append("<h3>COOKIES</h3>")
    for key, value in request.COOKIES.items():
        info.append(f"<b>{key}:</b> {value}")
    
    # Check session backend
    info.append("<h3>SESSION BACKEND</h3>")
    info.append(f"<b>Session engine:</b> {request.session.__class__}")
    
    return HttpResponse("<br>".join(info))