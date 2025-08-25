from datetime import timedelta
import logging

import pytz
from celery import shared_task
from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import UserProfile

logger = logging.getLogger(__name__)


@shared_task
def send_daily_workout_reminders():
    """Send daily workout reminders to users"""
    
    # Get current time in different timezones
    current_utc = timezone.now()
    
    # Get users who should receive reminders
    profiles = UserProfile.objects.filter(
        email_notifications_enabled=True,
        user__is_active=True,
        onboarding_completed_at__isnull=False
    ).select_related('user')
    
    sent_count = 0
    
    for profile in profiles:
        try:
            # Convert to user's timezone
            user_tz = pytz.timezone(profile.user.timezone)
            user_time = current_utc.astimezone(user_tz)
            
            # Check if it's notification time (within 5 minute window)
            notification_time = profile.notification_time
            current_time = user_time.time()
            
            # Calculate time difference in minutes
            notification_minutes = notification_time.hour * 60 + notification_time.minute
            current_minutes = current_time.hour * 60 + current_time.minute
            
            # Send if within 5 minute window
            if abs(current_minutes - notification_minutes) <= 5:
                
                # Check if user hasn't worked out today
                today = user_time.date()
                has_worked_out_today = profile.user.workout_executions.filter(
                    completed_at__date=today
                ).exists()
                
                if not has_worked_out_today:
                    send_workout_reminder_email(profile.user)
                    sent_count += 1
                    
        except Exception as e:
            # Log error but continue with other users
            logger.error(f"Error sending reminder to {profile.user.email}: {str(e)}")
            continue
    
    return f"Sent {sent_count} workout reminders"


def send_workout_reminder_email(user):
    """Send workout reminder email to specific user"""
    
    # Get today's workout
    active_plan = user.workout_plans.filter(is_active=True).first()
    if not active_plan:
        return
    
    current_week = active_plan.get_current_week()
    days_since_start = (timezone.now() - active_plan.started_at).days if active_plan.started_at else 0
    current_day = (days_since_start % 7) + 1
    
    today_workout = active_plan.daily_workouts.filter(
        week_number=current_week,
        day_number=current_day
    ).first()
    
    if not today_workout:
        return
    
    # Prepare email context
    context = {
        'user': user,
        'workout': today_workout,
        'streak': user.profile.current_streak,
        'workout_url': f"{settings.FRONTEND_URL}/workouts/daily/{today_workout.id}/"
    }
    
    # Render email templates
    subject = f"💪 Время тренировки, {user.first_name or user.username}!"
    
    html_message = render_to_string('emails/workout_reminder.html', context)
    text_message = render_to_string('emails/workout_reminder.txt', context)
    
    # Send email
    send_mail(
        subject=subject,
        message=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=True
    )


@shared_task
def send_achievement_notification(user_id, achievement_id):
    """Send achievement unlock notification"""
    from django.contrib.auth import get_user_model

    from apps.achievements.models import Achievement
    
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        achievement = Achievement.objects.get(id=achievement_id)
        
        if not user.profile.email_notifications_enabled:
            return "Email notifications disabled"
        
        context = {
            'user': user,
            'achievement': achievement,
            'dashboard_url': f"{settings.FRONTEND_URL}/dashboard/"
        }
        
        subject = f"🏆 Новое достижение: {achievement.name}!"
        
        html_message = render_to_string('emails/achievement_unlocked.html', context)
        text_message = render_to_string('emails/achievement_unlocked.txt', context)
        
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True
        )
        
        return f"Achievement notification sent to {user.email}"
        
    except Exception as e:
        return f"Error sending achievement notification: {str(e)}"


@shared_task
def send_weekly_progress_summary():
    """Send weekly progress summary to active users"""
    
    from apps.achievements.models import DailyProgress

    # Get users with activity in the last week
    week_ago = timezone.now() - timedelta(days=7)
    
    active_users = UserProfile.objects.filter(
        email_notifications_enabled=True,
        user__is_active=True,
        last_workout_at__gte=week_ago
    ).select_related('user')
    
    sent_count = 0
    
    for profile in active_users:
        try:
            user = profile.user
            
            # Get weekly stats
            weekly_progress = DailyProgress.objects.filter(
                user=user,
                date__gte=week_ago.date()
            ).aggregate(
                total_workouts=models.Sum('workouts_completed'),
                total_xp=models.Sum('xp_earned'),
                active_days=models.Count('id', filter=models.Q(workouts_completed__gt=0))
            )
            
            context = {
                'user': user,
                'weekly_stats': weekly_progress,
                'current_streak': profile.current_streak,
                'total_workouts': profile.total_workouts_completed,
                'dashboard_url': f"{settings.FRONTEND_URL}/dashboard/"
            }
            
            subject = "📊 Ваш прогресс за неделю"
            
            html_message = render_to_string('emails/weekly_summary.html', context)
            text_message = render_to_string('emails/weekly_summary.txt', context)
            
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=True
            )
            
            sent_count += 1
            
        except Exception as e:
            logger.error(f"Error sending weekly summary to {profile.user.email}: {str(e)}")
            continue
    
    return f"Sent {sent_count} weekly summaries"