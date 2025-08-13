"""
Management command to setup periodic tasks in django-celery-beat
"""
import json

from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = 'Setup periodic tasks for Celery Beat scheduler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing periodic tasks before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear_existing']:
            self.stdout.write('Clearing existing periodic tasks...')
            PeriodicTask.objects.all().delete()
            CrontabSchedule.objects.all().delete()

        # Create crontab schedules
        every_5_minutes, _ = CrontabSchedule.objects.get_or_create(
            minute='*/5',
            hour='*',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

        monday_8am, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='8',
            day_of_week='1',  # Monday
            day_of_month='*',
            month_of_year='*',
        )

        daily_1am, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='1',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

        sunday_2am, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='2',
            day_of_week='0',  # Sunday
            day_of_month='*',
            month_of_year='*',
        )

        # Create periodic tasks
        tasks_to_create = [
            {
                'name': 'enqueue-weekly-lesson',
                'task': 'apps.workouts.tasks.enqueue_weekly_lesson',
                'crontab': every_5_minutes,  # TEMP: Testing mode
                'description': 'Send weekly lessons to users (temporary: every 5 min for testing)'
            },
            {
                'name': 'send-amplitude-events-batch',
                'task': 'apps.analytics.tasks.batch_send_events_to_amplitude_task',
                'crontab': every_5_minutes,
                'description': 'Batch send analytics events to Amplitude'
            },
            {
                'name': 'calculate-daily-metrics',
                'task': 'apps.analytics.tasks.calculate_daily_metrics_task',
                'crontab': daily_1am,
                'description': 'Calculate daily metrics for analytics'
            },
            {
                'name': 'cleanup-old-analytics',
                'task': 'apps.analytics.tasks.cleanup_old_analytics_events_task',
                'crontab': sunday_2am,
                'description': 'Clean up old analytics events'
            },
            {
                'name': 'system-health-monitor',
                'task': 'apps.core.tasks.system_health_monitor_task',
                'crontab': every_5_minutes,
                'description': 'Monitor system health and send alerts'
            },
        ]

        created_count = 0
        for task_config in tasks_to_create:
            task, created = PeriodicTask.objects.get_or_create(
                name=task_config['name'],
                defaults={
                    'task': task_config['task'],
                    'crontab': task_config['crontab'],
                    'enabled': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created task: {task_config["name"]} - {task_config["description"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Task already exists: {task_config["name"]}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\nSetup complete! Created {created_count} new periodic tasks.')
        )
        self.stdout.write('Note: Weekly lesson task is in testing mode (every 5 minutes)')
        self.stdout.write('Run "python manage.py revert_weekly_schedule" to switch to production schedule')