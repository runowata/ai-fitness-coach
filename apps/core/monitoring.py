"""System monitoring and alerting for AI Fitness Coach"""
import time
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import requests
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from django.db import connection

logger = logging.getLogger(__name__)


class RedisHealthMonitor:
    """Monitor Redis performance and health"""
    
    def __init__(self):
        self.alert_threshold_ms = getattr(settings, 'REDIS_ALERT_THRESHOLD_MS', 100)
        self.test_key_prefix = 'health_check'
    
    def check_redis_latency(self) -> Dict:
        """
        Check Redis latency by performing get/set operations
        Returns latency metrics and health status
        """
        results = {
            'timestamp': timezone.now().isoformat(),
            'healthy': True,
            'latency_ms': None,
            'operations': {
                'set': {'time_ms': None, 'success': False},
                'get': {'time_ms': None, 'success': False},
                'delete': {'time_ms': None, 'success': False}
            },
            'alert_triggered': False,
            'error': None
        }
        
        test_key = f"{self.test_key_prefix}_{int(time.time())}"
        test_value = {'test': True, 'timestamp': timezone.now().isoformat()}
        
        try:
            # Test SET operation
            start_time = time.perf_counter()
            cache.set(test_key, test_value, timeout=60)
            set_time_ms = (time.perf_counter() - start_time) * 1000
            
            results['operations']['set']['time_ms'] = round(set_time_ms, 2)
            results['operations']['set']['success'] = True
            
            # Test GET operation
            start_time = time.perf_counter()
            cached_value = cache.get(test_key)
            get_time_ms = (time.perf_counter() - start_time) * 1000
            
            results['operations']['get']['time_ms'] = round(get_time_ms, 2)
            results['operations']['get']['success'] = cached_value is not None
            
            # Test DELETE operation
            start_time = time.perf_counter()
            cache.delete(test_key)
            delete_time_ms = (time.perf_counter() - start_time) * 1000
            
            results['operations']['delete']['time_ms'] = round(delete_time_ms, 2)
            results['operations']['delete']['success'] = True
            
            # Calculate overall latency (average of successful operations)
            successful_times = []
            for op_data in results['operations'].values():
                if op_data['success'] and op_data['time_ms'] is not None:
                    successful_times.append(op_data['time_ms'])
            
            if successful_times:
                results['latency_ms'] = round(sum(successful_times) / len(successful_times), 2)
            
            # Check alert threshold
            if results['latency_ms'] and results['latency_ms'] > self.alert_threshold_ms:
                results['alert_triggered'] = True
                results['healthy'] = False
            
        except Exception as e:
            results['healthy'] = False
            results['error'] = str(e)
            logger.error(f"Redis health check failed: {e}")
        
        return results
    
    def get_redis_info(self) -> Dict:
        """
        Get Redis server information (if available)
        Note: This requires direct Redis connection, not just Django cache
        """
        try:
            # Try to get Redis info through django-redis backend
            from django_redis import get_redis_connection
            
            redis_conn = get_redis_connection("default")
            info = redis_conn.info()
            
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', 'Unknown'),
                'redis_version': info.get('redis_version', 'Unknown'),
                'uptime_in_seconds': info.get('uptime_in_seconds', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
            }
            
        except ImportError:
            logger.warning("django-redis not available for detailed Redis info")
            return {'status': 'redis_info_unavailable'}
        except Exception as e:
            logger.error(f"Error getting Redis info: {e}")
            return {'error': str(e)}


class SlackAlerter:
    """Send alerts to Slack using webhook"""
    
    def __init__(self):
        self.webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', None)
        self.channel = getattr(settings, 'SLACK_ALERT_CHANNEL', '#alerts')
        self.username = getattr(settings, 'SLACK_BOT_USERNAME', 'AI-Fitness-Monitor')
        self.enabled = bool(self.webhook_url)
    
    def send_alert(
        self, 
        title: str, 
        message: str, 
        color: str = 'danger',
        fields: List[Dict] = None,
        include_timestamp: bool = True
    ) -> bool:
        """
        Send alert to Slack
        
        Args:
            title: Alert title
            message: Alert message
            color: Alert color (good, warning, danger)
            fields: Additional fields for the alert
            include_timestamp: Whether to include timestamp
        
        Returns:
            bool: Success status
        """
        if not self.enabled:
            logger.warning(f"Slack alerting disabled - Alert: {title}")
            return False
        
        # Prepare Slack payload
        attachment = {
            'color': color,
            'title': title,
            'text': message,
            'fields': fields or [],
        }
        
        if include_timestamp:
            attachment['ts'] = int(time.time())
        
        payload = {
            'channel': self.channel,
            'username': self.username,
            'attachments': [attachment]
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info(f"Slack alert sent successfully: {title}")
                return True
            else:
                logger.error(f"Slack alert failed: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Slack request error: {e}")
            return False
    
    def send_redis_latency_alert(self, redis_health: Dict) -> bool:
        """Send Redis latency alert to Slack"""
        latency = redis_health.get('latency_ms', 0)
        threshold = redis_health.get('alert_threshold_ms', 100)
        
        title = "🚨 Redis Performance Alert"
        message = f"Redis latency is {latency}ms, exceeding threshold of {threshold}ms"
        
        fields = [
            {
                'title': 'Current Latency',
                'value': f"{latency}ms",
                'short': True
            },
            {
                'title': 'Threshold',
                'value': f"{threshold}ms",
                'short': True
            },
            {
                'title': 'SET Operation',
                'value': f"{redis_health['operations']['set']['time_ms']}ms",
                'short': True
            },
            {
                'title': 'GET Operation',
                'value': f"{redis_health['operations']['get']['time_ms']}ms",
                'short': True
            }
        ]
        
        return self.send_alert(title, message, color='danger', fields=fields)
    
    def send_system_health_alert(self, component: str, status: str, details: str) -> bool:
        """Send general system health alert"""
        color_map = {
            'healthy': 'good',
            'warning': 'warning', 
            'degraded': 'warning',
            'error': 'danger',
            'critical': 'danger'
        }
        
        color = color_map.get(status, 'warning')
        icon_map = {
            'healthy': '✅',
            'warning': '⚠️',
            'degraded': '⚠️', 
            'error': '❌',
            'critical': '🚨'
        }
        
        icon = icon_map.get(status, '⚠️')
        
        title = f"{icon} System Health Alert: {component}"
        message = f"Status: {status.upper()}\n{details}"
        
        return self.send_alert(title, message, color=color)


class PerformanceMonitor:
    """Main performance monitoring class"""
    
    def __init__(self):
        self.redis_monitor = RedisHealthMonitor()
        self.slack_alerter = SlackAlerter()
        self.alert_cooldown_seconds = getattr(settings, 'ALERT_COOLDOWN_SECONDS', 300)  # 5 minutes
    
    def run_health_checks(self) -> Dict:
        """Run all health checks and return results"""
        results = {
            'timestamp': timezone.now().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }
        
        # Redis health check
        redis_health = self.redis_monitor.check_redis_latency()
        results['components']['redis'] = redis_health
        
        # Database health check
        db_health = self._check_database_health()
        results['components']['database'] = db_health
        
        # Determine overall status
        component_statuses = []
        for component, health in results['components'].items():
            if health.get('healthy', True):
                component_statuses.append('healthy')
            elif health.get('error'):
                component_statuses.append('error')
            else:
                component_statuses.append('degraded')
        
        if 'error' in component_statuses:
            results['overall_status'] = 'error'
        elif 'degraded' in component_statuses:
            results['overall_status'] = 'degraded'
        else:
            results['overall_status'] = 'healthy'
        
        return results
    
    def check_and_alert(self) -> Dict:
        """Run health checks and send alerts if necessary"""
        health_results = self.run_health_checks()
        alerts_sent = []
        
        # Check Redis latency alerts
        redis_health = health_results['components'].get('redis', {})
        if redis_health.get('alert_triggered') and not self._is_in_cooldown('redis_latency'):
            if self.slack_alerter.send_redis_latency_alert(redis_health):
                alerts_sent.append('redis_latency')
                self._set_alert_cooldown('redis_latency')
        
        # Check database alerts
        db_health = health_results['components'].get('database', {})
        if not db_health.get('healthy', True) and not self._is_in_cooldown('database_health'):
            details = f"Query time: {db_health.get('query_time_ms', 0)}ms"
            if db_health.get('error'):
                details += f"\nError: {db_health['error']}"
            
            if self.slack_alerter.send_system_health_alert('Database', 'error', details):
                alerts_sent.append('database_health')
                self._set_alert_cooldown('database_health')
        
        health_results['alerts_sent'] = alerts_sent
        return health_results
    
    def _check_database_health(self) -> Dict:
        """Check database performance"""
        try:
            start_time = time.perf_counter()
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            query_time_ms = (time.perf_counter() - start_time) * 1000
            
            return {
                'healthy': query_time_ms < 1000,  # 1 second threshold
                'query_time_ms': round(query_time_ms, 2),
                'connection_count': len(connection.queries)
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'healthy': False,
                'error': str(e),
                'query_time_ms': None
            }
    
    def _is_in_cooldown(self, alert_type: str) -> bool:
        """Check if alert type is in cooldown period"""
        cooldown_key = f"alert_cooldown:{alert_type}"
        return cache.get(cooldown_key) is not None
    
    def _set_alert_cooldown(self, alert_type: str):
        """Set cooldown period for alert type"""
        cooldown_key = f"alert_cooldown:{alert_type}"
        cache.set(cooldown_key, timezone.now().isoformat(), self.alert_cooldown_seconds)


class HealthEndpoint:
    """Provide health check endpoint data"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
    
    def get_health_status(self, include_details: bool = False) -> Dict:
        """Get health status for API endpoint"""
        try:
            health_results = self.monitor.run_health_checks()
            
            response = {
                'status': health_results['overall_status'],
                'timestamp': health_results['timestamp'],
                'version': getattr(settings, 'APP_VERSION', 'unknown')
            }
            
            if include_details:
                response['components'] = health_results['components']
            else:
                # Simplified component status
                response['components'] = {
                    name: {
                        'status': 'healthy' if data.get('healthy', True) else 'unhealthy',
                        'response_time_ms': data.get('latency_ms') or data.get('query_time_ms')
                    }
                    for name, data in health_results['components'].items()
                }
            
            return response
            
        except Exception as e:
            logger.error(f"Health endpoint error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }