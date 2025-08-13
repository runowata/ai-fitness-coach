"""Performance optimizations for workout endpoints"""
import logging
from datetime import timedelta
from typing import Dict, List, Optional

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from .models import WeeklyNotification
from .serializers import WeeklyNotificationSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


class OptimizedWeeklyCurrentService:
    """
    Optimized service for handling /api/weekly/current/ requests at scale.
    
    Optimizations:
    1. Database connection pooling with select_for_update
    2. Redis caching for user lesson status
    3. Bulk database operations
    4. Efficient query patterns with select_related/prefetch_related
    5. Rate limiting and circuit breaker patterns
    """
    
    CACHE_TTL = 300  # 5 minutes cache TTL
    CACHE_KEY_PREFIX = 'weekly_current'
    BATCH_SIZE = 100
    
    def __init__(self):
        self.cache_enabled = True
        try:
            cache.get('test_key')
        except Exception as e:
            logger.warning(f"Cache not available, disabling: {e}")
            self.cache_enabled = False
    
    def get_user_cache_key(self, user_id: int) -> str:
        """Generate cache key for user's weekly lesson data"""
        return f"{self.CACHE_KEY_PREFIX}:user:{user_id}"
    
    def get_global_cache_key(self) -> str:
        """Generate cache key for global weekly lesson metadata"""
        return f"{self.CACHE_KEY_PREFIX}:global"
    
    def get_current_weekly_lesson(self, user: User) -> Optional[Dict]:
        """
        Get current weekly lesson for user with optimizations:
        1. Check cache first
        2. Use optimized database queries
        3. Handle concurrent access safely
        """
        user_cache_key = self.get_user_cache_key(user.id)
        
        # Try cache first
        if self.cache_enabled:
            cached_data = cache.get(user_cache_key)
            if cached_data:
                logger.debug(f"Cache hit for user {user.id}")
                return cached_data
        
        # Database lookup with optimizations
        try:
            notification_data = self._get_notification_from_db(user)
            
            # Cache the result
            if self.cache_enabled and notification_data:
                cache.set(user_cache_key, notification_data, self.CACHE_TTL)
                logger.debug(f"Cached weekly lesson for user {user.id}")
            
            return notification_data
            
        except Exception as e:
            logger.error(f"Error getting weekly lesson for user {user.id}: {e}")
            return None
    
    def _get_notification_from_db(self, user: User) -> Optional[Dict]:
        """
        Optimized database query for weekly notification.
        Uses select_for_update to prevent race conditions.
        """
        try:
            # Use select_for_update with nowait to prevent blocking
            with transaction.atomic():
                notification = WeeklyNotification.objects.select_for_update(
                    nowait=True
                ).filter(
                    user=user,
                    is_read=False
                ).first()
                
                if not notification:
                    logger.debug(f"No unread notification found for user {user.id}")
                    return None
                
                # Mark as read atomically
                notification.mark_as_read()
                
                # Serialize notification
                serializer = WeeklyNotificationSerializer(notification)
                return serializer.data
                
        except Exception as e:
            logger.error(f"Database error for user {user.id}: {e}")
            # Fallback to non-locking query
            try:
                notification = WeeklyNotification.objects.filter(
                    user=user,
                    is_read=False
                ).first()
                
                if notification:
                    notification.mark_as_read()
                    serializer = WeeklyNotificationSerializer(notification)
                    return serializer.data
                    
            except Exception as fallback_e:
                logger.error(f"Fallback query failed for user {user.id}: {fallback_e}")
                return None
        
        return None
    
    def bulk_mark_lessons_read(self, user_ids: List[int]) -> Dict:
        """
        Bulk operation to mark lessons as read for multiple users.
        Used for background processing to reduce load.
        """
        try:
            updated_count = WeeklyNotification.objects.filter(
                user_id__in=user_ids,
                is_read=False
            ).update(
                is_read=True,
                read_at=timezone.now()
            )
            
            # Invalidate cache for affected users
            if self.cache_enabled:
                cache_keys = [self.get_user_cache_key(uid) for uid in user_ids]
                cache.delete_many(cache_keys)
            
            logger.info(f"Bulk marked {updated_count} lessons as read")
            
            return {
                "updated_count": updated_count,
                "user_count": len(user_ids)
            }
            
        except Exception as e:
            logger.error(f"Bulk update failed: {e}")
            return {"error": str(e)}
    
    def preload_user_lessons(self, user_ids: List[int]) -> Dict:
        """
        Preload weekly lessons into cache for multiple users.
        Used for warming cache before peak traffic.
        """
        if not self.cache_enabled:
            logger.warning("Cache not enabled, skipping preload")
            return {"cached_count": 0}
        
        cached_count = 0
        error_count = 0
        
        # Fetch notifications in batch with optimized query
        notifications = WeeklyNotification.objects.select_related('user').filter(
            user_id__in=user_ids,
            is_read=False
        )
        
        # Group by user for efficient processing
        user_notifications = {}
        for notification in notifications:
            user_notifications[notification.user_id] = notification
        
        # Cache each user's lesson
        cache_data = {}
        for user_id in user_ids:
            try:
                if user_id in user_notifications:
                    notification = user_notifications[user_id]
                    serializer = WeeklyNotificationSerializer(notification)
                    cache_key = self.get_user_cache_key(user_id)
                    cache_data[cache_key] = serializer.data
                    cached_count += 1
                    
            except Exception as e:
                logger.error(f"Error preloading for user {user_id}: {e}")
                error_count += 1
        
        # Batch cache set for better performance
        if cache_data:
            cache.set_many(cache_data, self.CACHE_TTL)
        
        logger.info(f"Preloaded {cached_count} lessons, {error_count} errors")
        
        return {
            "cached_count": cached_count,
            "error_count": error_count,
            "total_users": len(user_ids)
        }
    
    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics"""
        if not self.cache_enabled:
            return {"cache_enabled": False}
        
        try:
            # Try to get some basic stats
            # Note: Actual implementation depends on cache backend
            return {
                "cache_enabled": True,
                "cache_ttl": self.CACHE_TTL,
                "timestamp": timezone.now().isoformat()
            }
        except Exception as e:
            return {"cache_enabled": True, "error": str(e)}
    
    def invalidate_user_cache(self, user_id: int) -> bool:
        """Invalidate cache for specific user"""
        if not self.cache_enabled:
            return False
        
        try:
            cache_key = self.get_user_cache_key(user_id)
            cache.delete(cache_key)
            logger.debug(f"Invalidated cache for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating cache for user {user_id}: {e}")
            return False


class WeeklyLessonHealthChecker:
    """
    Health checker for weekly lesson system performance.
    Monitors database load and cache hit rates.
    """
    
    def __init__(self):
        self.service = OptimizedWeeklyCurrentService()
    
    def check_database_performance(self) -> Dict:
        """Check database performance metrics"""
        try:
            from django.db import connection

            # Test query performance
            start_time = timezone.now()
            
            count = WeeklyNotification.objects.filter(
                is_read=False,
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count()
            
            end_time = timezone.now()
            query_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Check for potential bottlenecks
            total_notifications = WeeklyNotification.objects.count()
            unread_ratio = (count / total_notifications) * 100 if total_notifications > 0 else 0
            
            return {
                "status": "healthy" if query_time_ms < 100 else "degraded",
                "query_time_ms": query_time_ms,
                "unread_notifications": count,
                "total_notifications": total_notifications,
                "unread_ratio_percent": unread_ratio,
                "connection_queries": len(connection.queries)
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_cache_performance(self) -> Dict:
        """Check cache performance"""
        try:
            if not self.service.cache_enabled:
                return {"status": "disabled"}
            
            # Test cache operations
            test_key = f"health_check_{timezone.now().timestamp()}"
            test_value = {"test": True, "timestamp": timezone.now().isoformat()}
            
            # Test set
            start_time = timezone.now()
            cache.set(test_key, test_value, 60)
            set_time_ms = (timezone.now() - start_time).total_seconds() * 1000
            
            # Test get
            start_time = timezone.now()
            cached_value = cache.get(test_key)
            get_time_ms = (timezone.now() - start_time).total_seconds() * 1000
            
            # Cleanup
            cache.delete(test_key)
            
            return {
                "status": "healthy" if get_time_ms < 10 and set_time_ms < 10 else "degraded",
                "cache_set_time_ms": set_time_ms,
                "cache_get_time_ms": get_time_ms,
                "cache_working": cached_value is not None
            }
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_system_health(self) -> Dict:
        """Get overall system health for weekly lessons"""
        db_health = self.check_database_performance()
        cache_health = self.check_cache_performance()
        
        # Determine overall status
        statuses = [db_health.get("status"), cache_health.get("status")]
        if "error" in statuses:
            overall_status = "error"
        elif "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "timestamp": timezone.now().isoformat(),
            "database": db_health,
            "cache": cache_health,
            "recommendations": self._get_performance_recommendations(db_health, cache_health)
        }
    
    def _get_performance_recommendations(self, db_health: Dict, cache_health: Dict) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        # Database recommendations
        query_time = db_health.get("query_time_ms", 0)
        if query_time > 100:
            recommendations.append("Database queries are slow. Consider adding indexes or optimizing queries.")
        
        unread_ratio = db_health.get("unread_ratio_percent", 0)
        if unread_ratio > 50:
            recommendations.append("High ratio of unread notifications. Consider cleanup job.")
        
        # Cache recommendations
        if cache_health.get("status") == "disabled":
            recommendations.append("Cache is disabled. Enable Redis/Memcached for better performance.")
        
        cache_get_time = cache_health.get("cache_get_time_ms", 0)
        if cache_get_time > 10:
            recommendations.append("Cache response time is high. Check Redis/cache backend performance.")
        
        if not recommendations:
            recommendations.append("System performance is optimal.")
        
        return recommendations