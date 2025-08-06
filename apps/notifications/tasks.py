"""Celery tasks for push notifications"""
from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
import logging

from .services import PushNotificationService
from apps.workouts.models import WeeklyNotification

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def send_push_notification_task(self, user_id: int, title: str, body: str, data: dict = None):
    """
    Send push notification to a specific user
    """
    try:
        user = User.objects.get(id=user_id)
        service = PushNotificationService()
        
        results = service.send_to_user(user, title, body, data or {})
        
        success_count = sum(1 for r in results if r.get("success"))
        total_count = len(results)
        
        logger.info(f"Push notification sent to {user.username}: {success_count}/{total_count} successful")
        
        return {
            "user_id": user_id,
            "title": title,
            "success_count": success_count,
            "total_count": total_count,
            "results": results
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for push notification")
        return {"error": f"User {user_id} not found"}
        
    except Exception as e:
        logger.error(f"Failed to send push notification to user {user_id}: {e}")
        # Retry the task
        self.retry(countdown=60 * (self.request.retries + 1), exc=e)


@shared_task(bind=True, max_retries=2)
def send_weekly_lesson_push_task(self, weekly_notification_id: int):
    """
    Send push notification for a new weekly lesson
    """
    try:
        notification = WeeklyNotification.objects.get(id=weekly_notification_id)
        service = PushNotificationService()
        
        results = service.send_weekly_lesson_notification(notification)
        
        success_count = sum(1 for r in results if r.get("success"))
        total_count = len(results)
        
        logger.info(f"Weekly lesson push sent to {notification.user.username}: {success_count}/{total_count} successful")
        
        return {
            "notification_id": weekly_notification_id,
            "user": notification.user.username,
            "week": notification.week,
            "success_count": success_count,
            "total_count": total_count,
            "results": results
        }
        
    except WeeklyNotification.DoesNotExist:
        logger.error(f"WeeklyNotification {weekly_notification_id} not found")
        return {"error": f"WeeklyNotification {weekly_notification_id} not found"}
        
    except Exception as e:
        logger.error(f"Failed to send weekly lesson push for {weekly_notification_id}: {e}")
        # Retry with exponential backoff
        self.retry(countdown=60 * (2 ** self.request.retries), exc=e)


@shared_task
def bulk_send_weekly_lesson_pushes_task(weekly_notification_ids: list):
    """
    Send push notifications for multiple weekly lessons in bulk
    """
    total_sent = 0
    total_failed = 0
    results = []
    
    for notification_id in weekly_notification_ids:
        try:
            # Queue individual task for each notification
            result = send_weekly_lesson_push_task.delay(notification_id)
            results.append({
                "notification_id": notification_id,
                "task_id": result.id,
                "status": "queued"
            })
            
        except Exception as e:
            logger.error(f"Failed to queue weekly lesson push for {notification_id}: {e}")
            results.append({
                "notification_id": notification_id,
                "status": "failed",
                "error": str(e)
            })
            total_failed += 1
    
    logger.info(f"Bulk weekly lesson push: {len(results) - total_failed} queued, {total_failed} failed")
    
    return {
        "total_queued": len(results) - total_failed,
        "total_failed": total_failed,
        "results": results
    }


@shared_task
def send_workout_reminder_push_task(user_id: int):
    """
    Send daily workout reminder push notification
    """
    try:
        user = User.objects.get(id=user_id)
        
        if not user.profile.push_notifications_enabled:
            logger.info(f"Push notifications disabled for user {user.username}")
            return {"status": "skipped", "reason": "notifications_disabled"}
        
        # Check if user has workout scheduled today
        from apps.workouts.models import WorkoutPlan
        active_plan = user.workout_plans.filter(is_active=True).first()
        
        if not active_plan:
            logger.info(f"No active workout plan for user {user.username}")
            return {"status": "skipped", "reason": "no_active_plan"}
        
        current_week = active_plan.get_current_week()
        today = timezone.now()
        days_since_start = (today - active_plan.started_at).days if active_plan.started_at else 0
        current_day = (days_since_start % 7) + 1
        
        today_workout = active_plan.daily_workouts.filter(
            week_number=current_week,
            day_number=current_day
        ).first()
        
        if not today_workout:
            logger.info(f"No workout scheduled today for user {user.username}")
            return {"status": "skipped", "reason": "no_workout_today"}
        
        # Send reminder notification
        title = "💪 Время тренировки!"
        body = f"Готов к сегодняшней тренировке? {today_workout.name}"
        
        data = {
            "type": "workout_reminder",
            "workout_id": today_workout.id,
            "week": current_week,
            "day": current_day
        }
        
        service = PushNotificationService()
        results = service.send_to_user(user, title, body, data)
        
        success_count = sum(1 for r in results if r.get("success"))
        
        return {
            "user_id": user_id,
            "workout_id": today_workout.id,
            "success_count": success_count,
            "total_count": len(results)
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for workout reminder")
        return {"error": f"User {user_id} not found"}
        
    except Exception as e:
        logger.error(f"Failed to send workout reminder to user {user_id}: {e}")
        return {"error": str(e)}


@shared_task
def cleanup_old_push_logs_task(days_to_keep: int = 30):
    """
    Clean up old push notification logs
    """
    from .models import PushNotificationLog
    
    cutoff_date = timezone.now() - timezone.timedelta(days=days_to_keep)
    
    deleted_count, _ = PushNotificationLog.objects.filter(
        sent_at__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old push notification logs")
    
    return {
        "deleted_count": deleted_count,
        "cutoff_date": cutoff_date.isoformat()
    }