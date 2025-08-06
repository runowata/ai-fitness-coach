"""Management command for system health monitoring and alerting"""
import time
import signal
import sys
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.monitoring import PerformanceMonitor


class Command(BaseCommand):
    help = 'Monitor system health and send alerts to Slack when thresholds are exceeded'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.running = True
        self.monitor = PerformanceMonitor()
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Check interval in seconds (default: 60)'
        )
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run as daemon (continuous monitoring)'
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=0,
            help='Total monitoring duration in seconds (0 = infinite for daemon mode)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run health checks without sending alerts'
        )
    
    def handle(self, *args, **options):
        self.verbose = options['verbose']
        self.dry_run = options['dry_run']
        interval = options['interval']
        daemon_mode = options['daemon']
        duration = options['duration']
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING("🧪 DRY RUN MODE - No alerts will be sent")
            )
        
        if daemon_mode:
            self.stdout.write("🔍 Starting System Health Monitor (Daemon Mode)")
        else:
            self.stdout.write("🔍 Running Single Health Check")
        
        self.stdout.write(f"⏱️  Check interval: {interval} seconds")
        if duration > 0:
            self.stdout.write(f"⏰ Total duration: {duration} seconds")
        
        start_time = time.time()
        check_count = 0
        alert_count = 0
        
        try:
            while self.running:
                check_count += 1
                
                if self.verbose:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.stdout.write(f"\n[{timestamp}] Running health check #{check_count}")
                
                # Run health checks and alerts
                try:
                    if self.dry_run:
                        health_results = self.monitor.run_health_checks()
                        alerts_would_send = self._check_alert_conditions(health_results)
                        
                        if alerts_would_send:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"⚠️  Would send alerts: {', '.join(alerts_would_send)}"
                                )
                            )
                        elif self.verbose:
                            self.stdout.write("✅ No alerts needed")
                    else:
                        health_results = self.monitor.check_and_alert()
                        alerts_sent = health_results.get('alerts_sent', [])
                        
                        if alerts_sent:
                            alert_count += len(alerts_sent)
                            self.stdout.write(
                                self.style.ERROR(
                                    f"🚨 Alerts sent: {', '.join(alerts_sent)}"
                                )
                            )
                        elif self.verbose:
                            self.stdout.write("✅ System healthy, no alerts sent")
                    
                    # Display health summary
                    if self.verbose:
                        self._display_health_summary(health_results)
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Health check failed: {e}")
                    )
                
                # Check if we should continue
                if not daemon_mode:
                    break
                
                if duration > 0 and (time.time() - start_time) >= duration:
                    self.stdout.write("⏰ Duration limit reached, stopping...")
                    break
                
                # Wait for next check
                if self.running:
                    time.sleep(interval)
            
        except KeyboardInterrupt:
            self.stdout.write("\n⚠️  Interrupted by user")
        
        # Final summary
        total_time = time.time() - start_time
        self.stdout.write("\n" + "="*50)
        self.stdout.write("📊 MONITORING SUMMARY")
        self.stdout.write("="*50)
        self.stdout.write(f"Total runtime: {total_time:.1f} seconds")
        self.stdout.write(f"Health checks: {check_count}")
        self.stdout.write(f"Alerts sent: {alert_count}")
        
        if check_count > 0:
            avg_interval = total_time / check_count if check_count > 1 else 0
            self.stdout.write(f"Average interval: {avg_interval:.1f} seconds")
        
        self.stdout.write("🏁 Monitoring completed")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        signal_names = {signal.SIGINT: 'SIGINT', signal.SIGTERM: 'SIGTERM'}
        signal_name = signal_names.get(signum, f'Signal {signum}')
        
        self.stdout.write(f"\n🛑 Received {signal_name}, shutting down gracefully...")
        self.running = False
    
    def _check_alert_conditions(self, health_results: dict) -> list:
        """Check what alerts would be sent (for dry-run mode)"""
        alerts_would_send = []
        
        # Check Redis latency
        redis_health = health_results['components'].get('redis', {})
        if redis_health.get('alert_triggered') and not self.monitor._is_in_cooldown('redis_latency'):
            alerts_would_send.append('redis_latency')
        
        # Check database health
        db_health = health_results['components'].get('database', {})
        if not db_health.get('healthy', True) and not self.monitor._is_in_cooldown('database_health'):
            alerts_would_send.append('database_health')
        
        return alerts_would_send
    
    def _display_health_summary(self, health_results: dict):
        """Display detailed health summary"""
        overall_status = health_results.get('overall_status', 'unknown')
        
        # Status styling
        if overall_status == 'healthy':
            status_display = self.style.SUCCESS(f"✅ {overall_status.upper()}")
        elif overall_status == 'degraded':
            status_display = self.style.WARNING(f"⚠️  {overall_status.upper()}")
        else:
            status_display = self.style.ERROR(f"❌ {overall_status.upper()}")
        
        self.stdout.write(f"Overall Status: {status_display}")
        
        # Component details
        components = health_results.get('components', {})
        
        for component_name, component_data in components.items():
            healthy = component_data.get('healthy', True)
            
            if component_name == 'redis':
                latency = component_data.get('latency_ms', 0)
                threshold = getattr(self.monitor.redis_monitor, 'alert_threshold_ms', 100)
                
                if healthy:
                    self.stdout.write(f"  Redis: ✅ {latency}ms (< {threshold}ms)")
                else:
                    self.stdout.write(f"  Redis: ❌ {latency}ms (> {threshold}ms)")
            
            elif component_name == 'database':
                query_time = component_data.get('query_time_ms', 0)
                
                if healthy:
                    self.stdout.write(f"  Database: ✅ {query_time}ms")
                else:
                    error = component_data.get('error', 'Performance issue')
                    self.stdout.write(f"  Database: ❌ {error}")
            
            else:
                status = "✅" if healthy else "❌"
                self.stdout.write(f"  {component_name}: {status}")


class HealthCheckCommand(Command):
    """Alias for single health check"""
    help = 'Run a single system health check'
    
    def handle(self, *args, **options):
        # Override options for single check
        options['daemon'] = False
        options['verbose'] = True
        
        super().handle(*args, **options)