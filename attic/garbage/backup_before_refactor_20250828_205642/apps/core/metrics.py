"""
Metrics collection module - abstraction over StatsD/OTEL/no-op

Provides simple interface for collecting metrics that can be sent to:
- StatsD (via django-statsd-mozilla)
- OpenTelemetry
- No-op (silent mode for development)
"""

import logging
import time
from functools import wraps
from typing import Any, Dict, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# Try to import StatsD client if available
try:
    from django_statsd.clients import statsd
    HAS_STATSD = True
except ImportError:
    HAS_STATSD = False
    statsd = None


class MetricsCollector:
    """Base metrics collector interface"""
    
    def incr(self, name: str, value: int = 1, tags: Optional[Dict[str, Any]] = None) -> None:
        """Increment a counter metric"""
    
    def timing(self, name: str, ms: float, tags: Optional[Dict[str, Any]] = None) -> None:
        """Record a timing metric in milliseconds"""
    
    def gauge(self, name: str, value: float, tags: Optional[Dict[str, Any]] = None) -> None:
        """Set a gauge metric to a specific value"""


class StatsDCollector(MetricsCollector):
    """StatsD metrics collector"""
    
    def incr(self, name: str, value: int = 1, tags: Optional[Dict[str, Any]] = None) -> None:
        """Increment counter in StatsD"""
        if statsd:
            # StatsD doesn't support tags natively, encode in metric name
            metric_name = self._encode_tags(name, tags)
            statsd.incr(metric_name, value)
    
    def timing(self, name: str, ms: float, tags: Optional[Dict[str, Any]] = None) -> None:
        """Record timing in StatsD"""
        if statsd:
            metric_name = self._encode_tags(name, tags)
            statsd.timing(metric_name, ms)
    
    def gauge(self, name: str, value: float, tags: Optional[Dict[str, Any]] = None) -> None:
        """Set gauge in StatsD"""
        if statsd:
            metric_name = self._encode_tags(name, tags)
            statsd.gauge(metric_name, value)
    
    def _encode_tags(self, name: str, tags: Optional[Dict[str, Any]]) -> str:
        """Encode tags into metric name for StatsD"""
        if not tags:
            return name
        # Format: metric.name.tag1_value1.tag2_value2
        tag_parts = [f"{k}_{v}" for k, v in tags.items()]
        return f"{name}.{'.'.join(tag_parts)}"


class LoggingCollector(MetricsCollector):
    """Debug collector that logs metrics"""
    
    def incr(self, name: str, value: int = 1, tags: Optional[Dict[str, Any]] = None) -> None:
        """Log counter increment"""
        logger.debug(f"METRIC INCR: {name}={value} tags={tags}")
    
    def timing(self, name: str, ms: float, tags: Optional[Dict[str, Any]] = None) -> None:
        """Log timing"""
        logger.debug(f"METRIC TIMING: {name}={ms}ms tags={tags}")
    
    def gauge(self, name: str, value: float, tags: Optional[Dict[str, Any]] = None) -> None:
        """Log gauge"""
        logger.debug(f"METRIC GAUGE: {name}={value} tags={tags}")


class NoOpCollector(MetricsCollector):
    """Silent no-op collector"""


# Initialize the appropriate collector based on settings
def _get_collector() -> MetricsCollector:
    """Factory to get the appropriate metrics collector"""
    metrics_backend = getattr(settings, 'METRICS_BACKEND', 'noop')
    
    if metrics_backend == 'statsd' and HAS_STATSD:
        return StatsDCollector()
    elif metrics_backend == 'logging' or settings.DEBUG:
        return LoggingCollector()
    else:
        return NoOpCollector()


# Global collector instance
_collector = _get_collector()


# Public API - simple functions for ease of use
def incr(name: str, value: int = 1, **tags) -> None:
    """Increment a counter metric
    
    Examples:
        incr('ai.whitelist.exercises_count', len(allowed))
        incr('video.provider.r2_count')
        incr('ai.plan.exercises_substituted', 5)
    """
    _collector.incr(name, value, tags if tags else None)


def timing(name: str, ms: float, **tags) -> None:
    """Record a timing metric in milliseconds
    
    Examples:
        timing('video.playlist.build_time_ms', 123.45)
        timing('ai.generation.duration_ms', 2500)
    """
    _collector.timing(name, ms, tags if tags else None)


def gauge(name: str, value: float, **tags) -> None:
    """Set a gauge metric to a specific value
    
    Examples:
        gauge('system.memory.used_mb', 512)
        gauge('users.active_count', 42)
    """
    _collector.gauge(name, value, tags if tags else None)


def timer(metric_name: str):
    """Decorator to time function execution
    
    Example:
        @timer('api.request.duration_ms')
        def process_request():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.monotonic()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.monotonic() - start) * 1000
                timing(metric_name, duration_ms)
        return wrapper
    return decorator


# Context manager for timing blocks
class Timer:
    """Context manager for timing code blocks
    
    Example:
        with Timer('database.query.duration_ms'):
            results = MyModel.objects.filter(...)
    """
    
    def __init__(self, metric_name: str, **tags):
        self.metric_name = metric_name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.monotonic()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.monotonic() - self.start_time) * 1000
            timing(self.metric_name, duration_ms, **self.tags)


# Pre-defined metric names for consistency
class MetricNames:
    """Standard metric names used across the application"""
    
    # AI metrics
    AI_WHITELIST_COUNT = 'ai.whitelist.exercises_count'
    AI_SUBSTITUTIONS = 'ai.plan.exercises_substituted'
    AI_VALIDATION_FAILED = 'ai.plan.validation_failed'
    AI_REPROMPTED = 'ai.plan.reprompted'
    AI_GENERATION_TIME = 'ai.generation.duration_ms'
    
    # Video metrics  
    VIDEO_PROVIDER_R2 = 'video.provider.r2_count'
    VIDEO_PROVIDER_STREAM = 'video.provider.stream_count'
    VIDEO_PLAYLIST_BUILD_TIME = 'video.playlist.build_time_ms'
    VIDEO_PLAYLIST_FALLBACKS = 'video.playlist.fallbacks'
    VIDEO_PLAYLIST_FALLBACK_HIT = 'video.playlist.fallback_hit'
    VIDEO_PLAYLIST_FALLBACK_MISSED = 'video.playlist.fallback_missed'
    VIDEO_PLAYLIST_CANDIDATES = 'video.playlist.candidates_found'
    VIDEO_SIGNED_URL_GENERATED = 'video.signed_url.generated'
    
    # System metrics
    SYSTEM_HEALTH_CHECK = 'system.health.check'
    SYSTEM_DB_QUERY_TIME = 'system.db.query_time_ms'