"""Celery tasks for core system functionality"""
import logging

from celery import shared_task

from .monitoring import PerformanceMonitor

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def system_health_monitor_task(self):
    """
    Celery task for periodic system health monitoring and alerting.
    Runs every 5 minutes to check Redis latency and other system metrics.
    Sends Slack alerts when thresholds are exceeded.
    """
    try:
        monitor = PerformanceMonitor()
        
        # Run health checks and send alerts if needed
        health_results = monitor.check_and_alert()
        
        # Log results
        overall_status = health_results.get('overall_status', 'unknown')
        alerts_sent = health_results.get('alerts_sent', [])
        
        if alerts_sent:
            logger.warning(f"System health monitor sent alerts: {', '.join(alerts_sent)}")
        else:
            logger.info(f"System health check completed: {overall_status}")
        
        # Return summary for Celery monitoring
        return {
            'status': 'completed',
            'overall_health': overall_status,
            'alerts_sent': alerts_sent,
            'timestamp': health_results.get('timestamp')
        }
        
    except Exception as e:
        logger.error(f"System health monitor task failed: {e}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)  # 1min, 2min, 4min
            self.retry(countdown=retry_delay, exc=e)
        
        # Send critical alert if all retries failed
        try:
            from .monitoring import SlackAlerter
            alerter = SlackAlerter()
            alerter.send_system_health_alert(
                'Health Monitor', 
                'critical', 
                f"Health monitoring task failed after {self.max_retries} retries: {str(e)}"
            )
        except Exception as alert_e:
            logger.error(f"Failed to send critical alert: {alert_e}")
        
        return {
            'status': 'failed',
            'error': str(e),
            'retries': self.request.retries
        }


@shared_task(bind=True, max_retries=2)
def send_slack_alert_task(
    self, 
    title: str, 
    message: str, 
    color: str = 'danger',
    fields: list = None
):
    """
    Celery task for sending Slack alerts asynchronously.
    This allows other parts of the system to queue alerts without blocking.
    """
    try:
        from .monitoring import SlackAlerter
        
        alerter = SlackAlerter()
        success = alerter.send_alert(
            title=title,
            message=message,
            color=color,
            fields=fields or []
        )
        
        if success:
            logger.info(f"Slack alert sent successfully: {title}")
            return {
                'status': 'sent',
                'title': title
            }
        else:
            logger.error(f"Failed to send Slack alert: {title}")
            return {
                'status': 'failed',
                'title': title,
                'error': 'Alert sending failed'
            }
            
    except Exception as e:
        logger.error(f"Slack alert task error: {e}")
        
        # Retry with short delay
        if self.request.retries < self.max_retries:
            self.retry(countdown=30, exc=e)
        
        return {
            'status': 'error',
            'title': title,
            'error': str(e),
            'retries': self.request.retries
        }


@shared_task
def redis_performance_test_task():
    """
    Test Redis performance and return metrics.
    Useful for debugging performance issues.
    """
    try:
        from .monitoring import RedisHealthMonitor
        
        monitor = RedisHealthMonitor()
        
        # Run multiple tests to get average
        results = []
        for i in range(5):
            result = monitor.check_redis_latency()
            if result.get('latency_ms'):
                results.append(result['latency_ms'])
        
        if results:
            avg_latency = sum(results) / len(results)
            max_latency = max(results)
            min_latency = min(results)
            
            logger.info(f"Redis performance test: avg={avg_latency:.2f}ms, max={max_latency:.2f}ms, min={min_latency:.2f}ms")
            
            return {
                'status': 'completed',
                'test_count': len(results),
                'average_latency_ms': round(avg_latency, 2),
                'max_latency_ms': round(max_latency, 2),
                'min_latency_ms': round(min_latency, 2),
                'all_results': results
            }
        else:
            logger.error("Redis performance test failed - no successful measurements")
            return {
                'status': 'failed',
                'error': 'No successful Redis operations'
            }
            
    except Exception as e:
        logger.error(f"Redis performance test task failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task
def system_stats_collection_task():
    """
    Collect system statistics for monitoring dashboards.
    Runs periodically to gather metrics for analysis.
    """
    try:
        from datetime import timedelta

        from django.contrib.auth import get_user_model
        from django.utils import timezone
        
        User = get_user_model()
        
        # Collect various system stats
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        
        stats = {
            'timestamp': now.isoformat(),
            'users': {
                'total': User.objects.count(),
                'active_today': User.objects.filter(last_login__gte=yesterday).count(),
                'new_today': User.objects.filter(date_joined__gte=yesterday).count(),
            },
            'system': {}
        }
        
        # Add health status
        from .monitoring import PerformanceMonitor
        monitor = PerformanceMonitor()
        health_results = monitor.run_health_checks()
        
        stats['system']['health_status'] = health_results['overall_status']
        stats['system']['redis_latency_ms'] = health_results.get('components', {}).get('redis', {}).get('latency_ms')
        stats['system']['database_query_time_ms'] = health_results.get('components', {}).get('database', {}).get('query_time_ms')
        
        logger.info(f"System stats collected: {stats['users']['total']} users, {stats['users']['active_today']} active today")
        
        return stats
        
    except Exception as e:
        logger.error(f"System stats collection failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }