from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, UserProfile


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Мы будем отправлять напоминания о тренировках')
    age_confirmed = forms.BooleanField(
        required=True,
        label='Я подтверждаю, что мне 18 лет или больше',
        error_messages={'required': 'Вы должны подтвердить свой возраст'}
    )
    agree_to_terms = forms.BooleanField(
        required=True,
        label='Я согласен с условиями использования и политикой конфиденциальности'
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_adult_confirmed = self.cleaned_data['age_confirmed']
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'notification_time',
            'push_notifications_enabled',
            'email_notifications_enabled',
        ]
        widgets = {
            'notification_time': forms.TimeInput(attrs={'type': 'time'}),
        }
        labels = {
            'notification_time': 'Время напоминания о тренировке',
            'push_notifications_enabled': 'Push-уведомления',
            'email_notifications_enabled': 'Email-уведомления',
        }