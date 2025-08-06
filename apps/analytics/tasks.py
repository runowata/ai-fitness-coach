"""Celery tasks for analytics processing"""
from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
import logging

from .models import AnalyticsEvent, AnalyticsMetrics
from .services import AmplitudeService

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def send_event_to_amplitude_task(self, event_id: int):
    """Send individual event to Amplitude"""
    try:
        event = AnalyticsEvent.objects.get(id=event_id)
        
        if event.amplitude_sent:
            logger.info(f"Event {event_id} already sent to Amplitude")
            return {"status": "already_sent", "event_id": event_id}
        
        amplitude = AmplitudeService()
        result = amplitude.send_event(event)
        
        if result.get("success"):
            logger.info(f"Event {event_id} sent to Amplitude successfully")
            return {"status": "sent", "event_id": event_id}
        else:
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Failed to send event {event_id} to Amplitude: {error_msg}")
            
            # Retry with exponential backoff
            if self.request.retries < self.max_retries:
                self.retry(countdown=60 * (2 ** self.request.retries), exc=Exception(error_msg))
            
            return {"status": "failed", "event_id": event_id, "error": error_msg}
            
    except AnalyticsEvent.DoesNotExist:
        logger.error(f"Event {event_id} not found")
        return {"status": "not_found", "event_id": event_id}
    except Exception as e:
        logger.error(f"Error sending event {event_id} to Amplitude: {e}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            self.retry(countdown=60 * (2 ** self.request.retries), exc=e)
        
        return {"status": "error", "event_id": event_id, "error": str(e)}


@shared_task
def batch_send_events_to_amplitude_task(batch_size: int = 10):
    """Send batch of pending events to Amplitude"""
    amplitude = AmplitudeService()
    
    # Get pending events
    pending_events = AnalyticsEvent.objects.filter(
        amplitude_sent=False,
        amplitude_error=''
    ).order_by('event_time')[:batch_size]
    
    if not pending_events:
        logger.info("No pending events to send to Amplitude")
        return {"status": "no_pending_events", "count": 0}
    
    events_list = list(pending_events)
    result = amplitude.send_events_batch(events_list)
    
    sent_count = result.get("sent_count", 0)
    total_count = len(events_list)
    
    logger.info(f"Amplitude batch send: {sent_count}/{total_count} events sent")
    
    return {
        "status": "completed",
        "total_events": total_count,
        "sent_count": sent_count,
        "success": result.get("success", False)
    }


@shared_task
def calculate_daily_metrics_task(date_str: str = None):
    """Calculate daily analytics metrics"""
    from datetime import datetime, timedelta
    
    if date_str:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        target_date = (timezone.now() - timedelta(days=1)).date()
    
    start_datetime = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
    end_datetime = start_datetime + timedelta(days=1)
    
    logger.info(f"Calculating daily metrics for {target_date}")
    
    # Daily Active Users
    dau = AnalyticsEvent.objects.filter(
        event_time__gte=start_datetime,
        event_time__lt=end_datetime,
        user__isnull=False
    ).values('user').distinct().count()
    
    AnalyticsMetrics.objects.update_or_create(
        metric_type='daily_active_users',
        metric_date=target_date,
        defaults={'metric_value': dau}
    )
    
    # Workout Completion Rate
    workouts_started = AnalyticsEvent.objects.filter(
        event_time__gte=start_datetime,
        event_time__lt=end_datetime,
        event_type='workout_started'
    ).count()
    
    workouts_completed = AnalyticsEvent.objects.filter(
        event_time__gte=start_datetime,
        event_time__lt=end_datetime,
        event_type='workout_completed'
    ).count()
    
    completion_rate = (workouts_completed / workouts_started * 100) if workouts_started > 0 else 0
    
    AnalyticsMetrics.objects.update_or_create(
        metric_type='workout_completion_rate',
        metric_date=target_date,
        defaults={'metric_value': completion_rate}
    )
    
    # Average Session Duration (in minutes)
    from .models import UserSession
    
    sessions = UserSession.objects.filter(
        started_at__gte=start_datetime,
        started_at__lt=end_datetime,
        duration_seconds__isnull=False
    )
    
    if sessions.exists():
        avg_duration = sessions.aggregate(avg=models.Avg('duration_seconds'))['avg']
        avg_duration_minutes = avg_duration / 60 if avg_duration else 0
    else:
        avg_duration_minutes = 0
    
    AnalyticsMetrics.objects.update_or_create(
        metric_type='average_session_duration',
        metric_date=target_date,
        defaults={'metric_value': avg_duration_minutes}
    )
    
    logger.info(f"Daily metrics calculated for {target_date}: DAU={dau}, Completion Rate={completion_rate:.1f}%, Avg Session={avg_duration_minutes:.1f}min")
    
    return {
        "date": target_date.isoformat(),
        "daily_active_users": dau,
        "workout_completion_rate": completion_rate,
        "average_session_duration_minutes": avg_duration_minutes
    }


@shared_task
def calculate_retention_metrics_task():
    """Calculate user retention metrics"""
    from datetime import datetime, timedelta
    
    today = timezone.now().date()
    
    # 7-day retention (users who signed up 7 days ago and were active today)
    seven_days_ago = today - timedelta(days=7)
    
    users_signed_up_7d_ago = User.objects.filter(
        date_joined__date=seven_days_ago
    )
    
    if users_signed_up_7d_ago.exists():
        active_today_from_7d_cohort = AnalyticsEvent.objects.filter(
            event_time__date=today,
            user__in=users_signed_up_7d_ago
        ).values('user').distinct().count()
        
        retention_7d = (active_today_from_7d_cohort / users_signed_up_7d_ago.count()) * 100
    else:
        retention_7d = 0
    
    AnalyticsMetrics.objects.update_or_create(
        metric_type='retention_rate',
        metric_date=today,
        dimension_filters={'period': '7d'},
        defaults={'metric_value': retention_7d}
    )
    
    # 30-day retention
    thirty_days_ago = today - timedelta(days=30)
    
    users_signed_up_30d_ago = User.objects.filter(
        date_joined__date=thirty_days_ago
    )
    
    if users_signed_up_30d_ago.exists():
        active_today_from_30d_cohort = AnalyticsEvent.objects.filter(
            event_time__date=today,
            user__in=users_signed_up_30d_ago
        ).values('user').distinct().count()
        
        retention_30d = (active_today_from_30d_cohort / users_signed_up_30d_ago.count()) * 100
    else:
        retention_30d = 0
    
    AnalyticsMetrics.objects.update_or_create(
        metric_type='retention_rate',
        metric_date=today,
        dimension_filters={'period': '30d'},
        defaults={'metric_value': retention_30d}
    )
    
    logger.info(f"Retention metrics calculated: 7d={retention_7d:.1f}%, 30d={retention_30d:.1f}%")
    
    return {
        "date": today.isoformat(),
        "retention_7d": retention_7d,
        "retention_30d": retention_30d
    }


@shared_task
def cleanup_old_analytics_events_task(days_to_keep: int = 90):
    """Clean up old analytics events to manage database size"""
    cutoff_date = timezone.now() - timezone.timedelta(days=days_to_keep)
    
    # Only delete events that have been successfully sent to Amplitude
    deleted_count, _ = AnalyticsEvent.objects.filter(
        event_time__lt=cutoff_date,
        amplitude_sent=True
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old analytics events (older than {days_to_keep} days)")
    
    return {
        "deleted_count": deleted_count,
        "cutoff_date": cutoff_date.isoformat()
    }


@shared_task
def generate_analytics_summary_task():
    """Generate daily analytics summary"""
    from datetime import timedelta
    
    yesterday = (timezone.now() - timedelta(days=1)).date()
    
    try:
        # Get metrics for yesterday
        dau_metric = AnalyticsMetrics.objects.filter(
            metric_type='daily_active_users',
            metric_date=yesterday
        ).first()
        
        completion_metric = AnalyticsMetrics.objects.filter(
            metric_type='workout_completion_rate', 
            metric_date=yesterday
        ).first()
        
        session_metric = AnalyticsMetrics.objects.filter(
            metric_type='average_session_duration',
            metric_date=yesterday
        ).first()
        
        # Get top events
        top_events = AnalyticsEvent.objects.filter(
            event_time__date=yesterday
        ).values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        summary = {
            "date": yesterday.isoformat(),
            "daily_active_users": dau_metric.metric_value if dau_metric else 0,
            "workout_completion_rate": completion_metric.metric_value if completion_metric else 0,
            "average_session_duration_minutes": session_metric.metric_value if session_metric else 0,
            "top_events": list(top_events),
            "total_events": AnalyticsEvent.objects.filter(event_time__date=yesterday).count()
        }
        
        logger.info(f"Analytics summary generated for {yesterday}: {summary}")
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating analytics summary for {yesterday}: {e}")
        return {"error": str(e), "date": yesterday.isoformat()}