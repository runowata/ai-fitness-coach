from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.urls import reverse
from .models import WeeklyLesson
from apps.users.models import User


@shared_task
def send_weekly_lesson():
    """
    Отправляет еженедельный урок всем активным пользователям.
    Запускается каждый понедельник в 09:00.
    """
    today = timezone.now()
    week_number = ((today - timezone.datetime(2024, 1, 1, tzinfo=timezone.utc)).days // 7) % 8 + 1
    
    active_users = User.objects.filter(is_active=True, profile__isnull=False)
    
    sent_count = 0
    for user in active_users:
        try:
            archetype = user.profile.archetype
            if not archetype:
                continue
                
            # Получаем урок для этого архетипа и недели
            lesson = WeeklyLesson.objects.filter(
                week=week_number,
                archetype=archetype,
                locale='ru'
            ).first()
            
            if lesson:
                # Подготавливаем контекст для шаблона
                base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'https://aifitnesscoach.com'
                context = {
                    'title': lesson.title,
                    'script': lesson.script,
                    'dashboard_url': f"{base_url}/users/dashboard/",
                    'profile_url': f"{base_url}/users/profile/",
                    'support_url': f"{base_url}/support/",
                    'unsubscribe_url': f"{base_url}/users/unsubscribe/",
                    'user': user,
                }
                
                # Рендерим HTML версию
                html_content = render_to_string('email/weekly_lesson.html', context)
                
                # Отправляем email
                send_mail(
                    subject=f'Урок недели {week_number}: {lesson.title}',
                    message=lesson.script,  # Plain text fallback
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_content,
                    fail_silently=False
                )
                sent_count += 1
                
        except Exception as e:
            # Логируем ошибку, но продолжаем отправку остальным
            print(f"Error sending weekly lesson to {user.email}: {e}")
            continue
    
    return f"Weekly lesson sent to {sent_count} users (week {week_number})"