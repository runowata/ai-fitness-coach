from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.urls import reverse
from datetime import datetime
import pytz
from .models import WeeklyLesson, WeeklyNotification
from apps.users.models import User


@shared_task
def send_weekly_lesson():
    """
    Отправляет еженедельный урок всем активным пользователям.
    Запускается каждый понедельник в 09:00.
    """
    today = timezone.now()
    week_number = ((today - datetime(2024, 1, 1, tzinfo=pytz.UTC)).days // 7) % 8 + 1
    
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


@shared_task
def enqueue_weekly_lesson():
    """
    НОВЫЙ ТАСК: Создает WeeklyNotification записи для всех активных пользователей.
    Заменяет send_weekly_lesson - теперь не шлем email, а создаем уведомления для фронтенда.
    Запускается каждый понедельник в 08:00 через Celery Beat.
    """
    today = timezone.now()
    week_number = ((today - datetime(2024, 1, 1, tzinfo=pytz.UTC)).days // 7) % 8 + 1
    
    active_users = User.objects.filter(is_active=True, profile__isnull=False)
    
    created_count = 0
    skipped_count = 0
    
    for user in active_users:
        try:
            archetype = user.profile.archetype
            if not archetype:
                skipped_count += 1
                continue
                
            # Проверяем, нет ли уже уведомления для этого пользователя и недели
            existing = WeeklyNotification.objects.filter(
                user=user,
                week=week_number
            ).exists()
            
            if existing:
                skipped_count += 1
                continue
                
            # Получаем урок для этого архетипа и недели
            lesson = WeeklyLesson.objects.filter(
                week=week_number,
                archetype=archetype,
                locale='ru'
            ).first()
            
            if lesson:
                # Создаем уведомление
                weekly_notification = WeeklyNotification.objects.create(
                    user=user,
                    week=week_number,
                    archetype=archetype,
                    lesson_title=lesson.title,
                    lesson_script=lesson.script
                )
                created_count += 1
                
                # Отправляем push-уведомление (если пользователь подписан)
                try:
                    from apps.notifications.tasks import send_weekly_lesson_push_task
                    send_weekly_lesson_push_task.delay(weekly_notification.id)
                except ImportError:
                    print(f"Push notification service not available for user {user.email}")
                except Exception as push_e:
                    print(f"Error queuing push notification for {user.email}: {push_e}")
            else:
                print(f"No lesson found for week {week_number}, archetype {archetype}")
                skipped_count += 1
                
        except Exception as e:
            # Логируем ошибку, но продолжаем создание для остальных
            print(f"Error creating weekly notification for {user.email}: {e}")
            skipped_count += 1
            continue
    
    return f"Weekly notifications: Created {created_count}, Skipped {skipped_count} (week {week_number})"