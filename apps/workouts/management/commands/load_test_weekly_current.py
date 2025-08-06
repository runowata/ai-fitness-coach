"""Management command for load testing /api/weekly/current/ endpoint"""
import time
import asyncio
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.workouts.models import WeeklyNotification, WeeklyLesson
from apps.workouts.performance import OptimizedWeeklyCurrentService, WeeklyLessonHealthChecker

User = get_user_model()


class Command(BaseCommand):
    help = 'Load test the /api/weekly/current/ endpoint for performance optimization'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=100,
            help='Number of concurrent users to simulate (default: 100)'
        )
        parser.add_argument(
            '--requests',
            type=int,
            default=10,
            help='Number of requests per user (default: 10)'
        )
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Create test users and notifications before testing'
        )
        parser.add_argument(
            '--use-optimized',
            action='store_true',
            help='Test the optimized version of the endpoint'
        )
        parser.add_argument(
            '--warmup-cache',
            action='store_true',
            help='Warm up cache before testing'
        )
        parser.add_argument(
            '--max-workers',
            type=int,
            default=50,
            help='Maximum number of worker threads (default: 50)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write("🚀 Starting Weekly Current API Load Test")
        
        num_users = options['users']
        requests_per_user = options['requests']
        max_workers = min(options['max_workers'], num_users)
        
        # Create test data if requested
        if options['create_test_data']:
            self.stdout.write("📊 Creating test data...")
            test_users = self.create_test_data(num_users)
        else:
            # Use existing users
            test_users = list(User.objects.filter(is_active=True)[:num_users])
            if len(test_users) < num_users:
                self.stdout.write(
                    self.style.WARNING(
                        f"Only found {len(test_users)} users, expected {num_users}. "
                        f"Use --create-test-data to create test users."
                    )
                )
                return
        
        self.stdout.write(f"👥 Using {len(test_users)} test users")
        
        # Warm up cache if requested
        if options['warmup_cache']:
            self.stdout.write("🔥 Warming up cache...")
            self.warmup_cache([u.id for u in test_users])
        
        # Run health check before testing
        self.stdout.write("🔍 Running pre-test health check...")
        health_checker = WeeklyLessonHealthChecker()
        pre_health = health_checker.get_system_health()
        self.stdout.write(f"Pre-test health: {pre_health['overall_status']}")
        
        # Run load test
        self.stdout.write(f"⚡ Starting load test: {num_users} users × {requests_per_user} requests")
        self.stdout.write(f"🧵 Using {max_workers} worker threads")
        
        start_time = time.time()
        
        # Run concurrent requests
        results = self.run_concurrent_test(
            test_users, 
            requests_per_user, 
            max_workers,
            options['use_optimized']
        )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        self.analyze_results(results, total_time, num_users, requests_per_user)
        
        # Run health check after testing
        self.stdout.write("🔍 Running post-test health check...")
        post_health = health_checker.get_system_health()
        self.stdout.write(f"Post-test health: {post_health['overall_status']}")
        
        # Compare performance
        self.compare_health_metrics(pre_health, post_health)
    
    def create_test_data(self, num_users: int) -> List[User]:
        """Create test users and weekly notifications"""
        users = []
        
        # Create test users
        for i in range(num_users):
            username = f"loadtest_user_{i}"
            email = f"loadtest_{i}@example.com"
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_active': True,
                    'completed_onboarding': True
                }
            )
            
            if created:
                # Create user profile
                if hasattr(user, 'profile'):
                    user.profile.archetype = ['111', '222', '333'][i % 3]
                    user.profile.save()
            
            users.append(user)
        
        self.stdout.write(f"✅ Created/found {len(users)} test users")
        
        # Create weekly notifications for users who don't have them
        notifications_created = 0
        
        for user in users:
            if not WeeklyNotification.objects.filter(user=user, is_read=False).exists():
                WeeklyNotification.objects.create(
                    user=user,
                    week=1,
                    archetype=getattr(user.profile, 'archetype', '111'),
                    lesson_title=f"Test Lesson for {user.username}",
                    lesson_script=f"This is a test lesson script for load testing user {user.username}."
                )
                notifications_created += 1
        
        self.stdout.write(f"✅ Created {notifications_created} weekly notifications")
        
        return users
    
    def warmup_cache(self, user_ids: List[int]):
        """Warm up cache with user data"""
        service = OptimizedWeeklyCurrentService()
        result = service.preload_user_lessons(user_ids)
        
        self.stdout.write(
            f"🔥 Cache warmed up: {result['cached_count']} lessons cached, "
            f"{result.get('error_count', 0)} errors"
        )
    
    def run_concurrent_test(
        self, 
        users: List[User], 
        requests_per_user: int, 
        max_workers: int,
        use_optimized: bool
    ) -> List[Dict]:
        """Run concurrent requests using ThreadPoolExecutor"""
        
        all_results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = []
            
            for user in users:
                for request_num in range(requests_per_user):
                    future = executor.submit(
                        self.make_request, 
                        user, 
                        request_num,
                        use_optimized
                    )
                    futures.append(future)
            
            # Collect results with progress indication
            completed = 0
            total_requests = len(users) * requests_per_user
            
            for future in as_completed(futures):
                result = future.result()
                all_results.append(result)
                completed += 1
                
                # Progress indicator
                if completed % 100 == 0:
                    progress = (completed / total_requests) * 100
                    self.stdout.write(f"📈 Progress: {completed}/{total_requests} ({progress:.1f}%)")
        
        return all_results
    
    def make_request(self, user: User, request_num: int, use_optimized: bool = False) -> Dict:
        """Make a single request to the weekly current endpoint"""
        client = Client()
        client.force_login(user)
        
        url = reverse('api_weekly_current')
        
        start_time = time.time()
        
        try:
            if use_optimized:
                # Test the optimized service directly
                from apps.workouts.performance import OptimizedWeeklyCurrentService
                service = OptimizedWeeklyCurrentService()
                lesson_data = service.get_current_weekly_lesson(user)
                
                if lesson_data:
                    status_code = 200
                    response_size = len(str(lesson_data))
                else:
                    status_code = 404
                    response_size = 0
            else:
                # Test via HTTP endpoint
                response = client.get(url)
                status_code = response.status_code
                response_size = len(response.content)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # milliseconds
            
            return {
                'user_id': user.id,
                'request_num': request_num,
                'status_code': status_code,
                'response_time_ms': response_time,
                'response_size': response_size,
                'success': status_code in [200, 404],  # Both are valid responses
                'error': None
            }
            
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            return {
                'user_id': user.id,
                'request_num': request_num,
                'status_code': 500,
                'response_time_ms': response_time,
                'response_size': 0,
                'success': False,
                'error': str(e)
            }
    
    def analyze_results(
        self, 
        results: List[Dict], 
        total_time: float, 
        num_users: int, 
        requests_per_user: int
    ):
        """Analyze and display test results"""
        
        # Basic statistics
        total_requests = len(results)
        successful_requests = len([r for r in results if r['success']])
        failed_requests = total_requests - successful_requests
        
        response_times = [r['response_time_ms'] for r in results if r['success']]
        
        if not response_times:
            self.stdout.write(self.style.ERROR("❌ No successful requests to analyze!"))
            return
        
        # Calculate percentiles
        p50 = statistics.median(response_times)
        p95 = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times)
        p99 = statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else max(response_times)
        
        # Calculate throughput
        requests_per_second = total_requests / total_time
        
        # Status code breakdown
        status_codes = {}
        for result in results:
            code = result['status_code']
            status_codes[code] = status_codes.get(code, 0) + 1
        
        # Display results
        self.stdout.write("\n" + "="*60)
        self.stdout.write("📊 LOAD TEST RESULTS")
        self.stdout.write("="*60)
        
        self.stdout.write(f"👥 Users: {num_users}")
        self.stdout.write(f"🔄 Requests per user: {requests_per_user}")
        self.stdout.write(f"📝 Total requests: {total_requests}")
        self.stdout.write(f"⏱️  Total time: {total_time:.2f}s")
        self.stdout.write(f"⚡ Requests/second: {requests_per_second:.2f}")
        
        self.stdout.write(f"\n🎯 SUCCESS RATE:")
        self.stdout.write(f"✅ Successful: {successful_requests} ({successful_requests/total_requests*100:.1f}%)")
        self.stdout.write(f"❌ Failed: {failed_requests} ({failed_requests/total_requests*100:.1f}%)")
        
        self.stdout.write(f"\n📈 RESPONSE TIMES (ms):")
        self.stdout.write(f"Average: {statistics.mean(response_times):.2f}")
        self.stdout.write(f"Median (P50): {p50:.2f}")
        self.stdout.write(f"95th percentile: {p95:.2f}")
        self.stdout.write(f"99th percentile: {p99:.2f}")
        self.stdout.write(f"Min: {min(response_times):.2f}")
        self.stdout.write(f"Max: {max(response_times):.2f}")
        
        self.stdout.write(f"\n📊 STATUS CODES:")
        for code, count in sorted(status_codes.items()):
            percentage = (count / total_requests) * 100
            self.stdout.write(f"{code}: {count} ({percentage:.1f}%)")
        
        # Performance assessment
        self.stdout.write(f"\n🏆 PERFORMANCE ASSESSMENT:")
        
        if p95 < 100:
            self.stdout.write(self.style.SUCCESS("✅ Excellent: P95 < 100ms"))
        elif p95 < 500:
            self.stdout.write(self.style.WARNING("⚠️  Good: P95 < 500ms"))
        elif p95 < 1000:
            self.stdout.write(self.style.WARNING("⚠️  Acceptable: P95 < 1s"))
        else:
            self.stdout.write(self.style.ERROR("❌ Poor: P95 > 1s"))
        
        if requests_per_second > 100:
            self.stdout.write(self.style.SUCCESS("✅ High throughput: >100 req/s"))
        elif requests_per_second > 50:
            self.stdout.write(self.style.WARNING("⚠️  Medium throughput: >50 req/s"))
        else:
            self.stdout.write(self.style.ERROR("❌ Low throughput: <50 req/s"))
        
        if failed_requests / total_requests < 0.01:
            self.stdout.write(self.style.SUCCESS("✅ Low error rate: <1%"))
        elif failed_requests / total_requests < 0.05:
            self.stdout.write(self.style.WARNING("⚠️  Moderate error rate: <5%"))
        else:
            self.stdout.write(self.style.ERROR("❌ High error rate: >5%"))
        
        self.stdout.write("="*60)
    
    def compare_health_metrics(self, pre_health: Dict, post_health: Dict):
        """Compare pre and post test health metrics"""
        self.stdout.write("\n🔍 SYSTEM HEALTH COMPARISON:")
        
        pre_db = pre_health.get('database', {})
        post_db = post_health.get('database', {})
        
        pre_query_time = pre_db.get('query_time_ms', 0)
        post_query_time = post_db.get('query_time_ms', 0)
        
        if post_query_time > pre_query_time * 2:
            self.stdout.write(self.style.ERROR("❌ Database performance degraded significantly"))
        elif post_query_time > pre_query_time * 1.5:
            self.stdout.write(self.style.WARNING("⚠️  Database performance slightly degraded"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ Database performance stable"))
        
        self.stdout.write(f"DB query time: {pre_query_time:.1f}ms → {post_query_time:.1f}ms")
        
        # Cache comparison
        pre_cache = pre_health.get('cache', {})
        post_cache = post_health.get('cache', {})
        
        if pre_cache.get('status') == 'healthy' and post_cache.get('status') != 'healthy':
            self.stdout.write(self.style.ERROR("❌ Cache performance degraded"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ Cache performance stable"))
        
        # Recommendations
        recommendations = post_health.get('recommendations', [])
        if recommendations:
            self.stdout.write(f"\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                self.stdout.write(f"• {rec}")