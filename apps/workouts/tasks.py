from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
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
                send_mail(
                    subject=f'Урок недели {week_number}: {lesson.title}',
                    message=lesson.script,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False
                )
                sent_count += 1
                
        except Exception as e:
            # Логируем ошибку, но продолжаем отправку остальным
            print(f"Error sending weekly lesson to {user.email}: {e}")
            continue
    
    return f"Weekly lesson sent to {sent_count} users"