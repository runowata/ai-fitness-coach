"""Management command for monitoring weekly lesson endpoint performance"""
import time
import json
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model

from apps.workouts.models import WeeklyNotification
from apps.workouts.performance import WeeklyLessonHealthChecker, OptimizedWeeklyCurrentService

User = get_user_model()


class Command(BaseCommand):
    help = 'Monitor performance of weekly lesson system and provide optimization insights'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Monitoring interval in seconds (default: 60)'
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=300,
            help='Total monitoring duration in seconds (default: 300 = 5 minutes)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file for performance data (JSON format)'
        )
        parser.add_argument(
            '--alert-threshold-ms',
            type=float,
            default=500.0,
            help='Alert threshold for response time in milliseconds (default: 500)'
        )
        parser.add_argument(
            '--cache-warmup',
            action='store_true',
            help='Warm up cache before monitoring'
        )
    
    def handle(self, *args, **options):
        self.stdout.write("🔍 Starting Weekly Lesson Performance Monitor")
        
        interval = options['interval']
        duration = options['duration']
        alert_threshold = options['alert_threshold_ms']
        output_file = options['output']
        
        # Initialize components
        health_checker = WeeklyLessonHealthChecker()
        service = OptimizedWeeklyCurrentService()
        
        # Cache warmup if requested
        if options['cache_warmup']:
            self.stdout.write("🔥 Warming up cache...")
            active_users = list(User.objects.filter(
                is_active=True,
                weekly_notifications__is_read=False
            ).values_list('id', flat=True)[:100])
            
            if active_users:
                warmup_result = service.preload_user_lessons(active_users)
                self.stdout.write(
                    f"Cache warmed: {warmup_result['cached_count']} lessons, "
                    f"{warmup_result.get('error_count', 0)} errors"
                )
        
        # Start monitoring
        self.stdout.write(f"📊 Monitoring for {duration}s with {interval}s intervals")
        self.stdout.write(f"🚨 Alert threshold: {alert_threshold}ms")
        
        start_time = time.time()
        monitoring_data = []
        
        while time.time() - start_time < duration:
            cycle_start = time.time()
            
            # Collect metrics
            health_data = health_checker.get_system_health()
            cache_stats = service.get_cache_stats()
            system_metrics = self.collect_system_metrics()
            
            # Combine data
            data_point = {
                'timestamp': timezone.now().isoformat(),
                'elapsed_time': time.time() - start_time,
                'health': health_data,
                'cache': cache_stats,
                'system': system_metrics
            }
            
            monitoring_data.append(data_point)
            
            # Display current status
            self.display_current_status(data_point, alert_threshold)
            
            # Check for alerts
            self.check_alerts(data_point, alert_threshold)
            
            # Wait for next interval
            cycle_time = time.time() - cycle_start
            sleep_time = max(0, interval - cycle_time)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # Generate final report
        self.generate_final_report(monitoring_data, alert_threshold)
        
        # Save data to file if requested
        if output_file:
            self.save_monitoring_data(monitoring_data, output_file)
            self.stdout.write(f"💾 Monitoring data saved to {output_file}")
    
    def collect_system_metrics(self) -> dict:
        """Collect system-level metrics"""
        from django.db import connection
        
        try:
            # Database metrics
            with connection.cursor() as cursor:
                # Count of unread notifications
                cursor.execute("""
                    SELECT COUNT(*) FROM weekly_notifications 
                    WHERE is_read = false AND created_at > %s
                """, [timezone.now() - timedelta(days=7)])
                unread_count = cursor.fetchone()[0]
                
                # Average notification age
                cursor.execute("""
                    SELECT AVG(EXTRACT(EPOCH FROM (NOW() - created_at))) 
                    FROM weekly_notifications 
                    WHERE is_read = false
                """)
                avg_age_seconds = cursor.fetchone()[0] or 0
                
                # Active users with notifications
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) FROM weekly_notifications 
                    WHERE is_read = false AND created_at > %s
                """, [timezone.now() - timedelta(days=1)])
                active_users = cursor.fetchone()[0]
            
            return {
                'unread_notifications': unread_count,
                'avg_notification_age_hours': avg_age_seconds / 3600,
                'active_users_with_notifications': active_users,
                'database_queries_count': len(connection.queries),
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def display_current_status(self, data_point: dict, alert_threshold: float):
        """Display current monitoring status"""
        elapsed = data_point['elapsed_time']
        health = data_point['health']
        
        # Extract key metrics
        db_status = health.get('database', {}).get('status', 'unknown')
        cache_status = health.get('cache', {}).get('status', 'unknown')
        query_time = health.get('database', {}).get('query_time_ms', 0)
        
        # Format output
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        self.stdout.write(
            f"[{timestamp}] +{elapsed:.0f}s | "
            f"DB: {db_status} ({query_time:.1f}ms) | "
            f"Cache: {cache_status} | "
            f"Health: {health.get('overall_status', 'unknown')}"
        )
    
    def check_alerts(self, data_point: dict, alert_threshold: float):
        """Check for performance alerts"""
        health = data_point['health']
        db_health = health.get('database', {})
        cache_health = health.get('cache', {})
        
        # Database performance alert
        query_time = db_health.get('query_time_ms', 0)
        if query_time > alert_threshold:
            self.stdout.write(
                self.style.ERROR(
                    f"🚨 ALERT: Database query time {query_time:.1f}ms > {alert_threshold}ms"
                )
            )
        
        # Cache performance alert
        cache_get_time = cache_health.get('cache_get_time_ms', 0)
        if cache_get_time > 50:  # Cache should be very fast
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  Cache slow: {cache_get_time:.1f}ms"
                )
            )
        
        # Error status alert
        if health.get('overall_status') == 'error':
            self.stdout.write(
                self.style.ERROR(
                    "🚨 ALERT: System health status is ERROR"
                )
            )
        
        # High unread notifications alert
        system_metrics = data_point.get('system', {})
        unread_count = system_metrics.get('unread_notifications', 0)
        if unread_count > 1000:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  High unread notifications: {unread_count}"
                )
            )
    
    def generate_final_report(self, monitoring_data: list, alert_threshold: float):
        """Generate final monitoring report"""
        if not monitoring_data:
            self.stdout.write("No monitoring data collected")
            return
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write("📊 PERFORMANCE MONITORING REPORT")
        self.stdout.write("="*60)
        
        # Calculate averages
        query_times = []
        cache_get_times = []
        unread_counts = []
        
        for data_point in monitoring_data:
            health = data_point['health']
            db_health = health.get('database', {})
            cache_health = health.get('cache', {})
            system_metrics = data_point.get('system', {})
            
            if 'query_time_ms' in db_health:
                query_times.append(db_health['query_time_ms'])
            
            if 'cache_get_time_ms' in cache_health:
                cache_get_times.append(cache_health['cache_get_time_ms'])
            
            if 'unread_notifications' in system_metrics:
                unread_counts.append(system_metrics['unread_notifications'])
        
        # Display averages
        if query_times:
            avg_query_time = sum(query_times) / len(query_times)
            max_query_time = max(query_times)
            self.stdout.write(f"🗄️  Database Query Times:")
            self.stdout.write(f"   Average: {avg_query_time:.2f}ms")
            self.stdout.write(f"   Maximum: {max_query_time:.2f}ms")
            self.stdout.write(f"   Samples: {len(query_times)}")
            
            if max_query_time > alert_threshold:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Max exceeded threshold ({alert_threshold}ms)")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ Within threshold ({alert_threshold}ms)")
                )
        
        if cache_get_times:
            avg_cache_time = sum(cache_get_times) / len(cache_get_times)
            self.stdout.write(f"\n🚄 Cache Performance:")
            self.stdout.write(f"   Average get time: {avg_cache_time:.2f}ms")
            self.stdout.write(f"   Samples: {len(cache_get_times)}")
            
            if avg_cache_time > 20:
                self.stdout.write(
                    self.style.WARNING("   ⚠️  Cache performance degraded")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("   ✅ Cache performance good")
                )
        
        if unread_counts:
            avg_unread = sum(unread_counts) / len(unread_counts)
            max_unread = max(unread_counts)
            self.stdout.write(f"\n📬 Unread Notifications:")
            self.stdout.write(f"   Average: {avg_unread:.0f}")
            self.stdout.write(f"   Maximum: {max_unread}")
            
            if max_unread > 500:
                self.stdout.write(
                    self.style.WARNING("   ⚠️  Consider cleanup job")
                )
        
        # Health status summary
        health_statuses = [dp['health']['overall_status'] for dp in monitoring_data]
        healthy_count = health_statuses.count('healthy')
        total_count = len(health_statuses)
        
        self.stdout.write(f"\n🏥 System Health:")
        self.stdout.write(f"   Healthy samples: {healthy_count}/{total_count} ({healthy_count/total_count*100:.1f}%)")
        
        if healthy_count == total_count:
            self.stdout.write(
                self.style.SUCCESS("   ✅ System consistently healthy")
            )
        elif healthy_count / total_count > 0.8:
            self.stdout.write(
                self.style.WARNING("   ⚠️  System mostly healthy with some issues")
            )
        else:
            self.stdout.write(
                self.style.ERROR("   ❌ System health issues detected")
            )
        
        # Optimization recommendations
        self.stdout.write(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
        
        if query_times and max(query_times) > 200:
            self.stdout.write("   • Consider database query optimization or indexing")
        
        if cache_get_times and max(cache_get_times) > 30:
            self.stdout.write("   • Check Redis/cache backend performance")
        
        if unread_counts and max(unread_counts) > 1000:
            self.stdout.write("   • Implement cleanup job for old notifications")
        
        if not any([query_times, cache_get_times]):
            self.stdout.write("   • Monitor system during higher load for better insights")
        
        self.stdout.write("="*60)
    
    def save_monitoring_data(self, monitoring_data: list, output_file: str):
        """Save monitoring data to JSON file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(monitoring_data, f, indent=2, default=str)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error saving to {output_file}: {e}")
            )