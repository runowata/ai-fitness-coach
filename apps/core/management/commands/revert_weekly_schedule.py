"""
Management command to revert weekly lesson schedule to production (Monday 8:00 AM)
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = 'Revert weekly lesson schedule from testing (every 5 min) to production (Monday 8:00 AM)'

    def handle(self, *args, **options):
        try:
            # Find the weekly lesson task
            task = PeriodicTask.objects.get(name='enqueue-weekly-lesson')
            
            # Create or get Monday 8:00 AM schedule
            monday_8am, created = CrontabSchedule.objects.get_or_create(
                minute='0',
                hour='8',
                day_of_week='1',  # Monday
                day_of_month='*',
                month_of_year='*',
            )
            
            # Update the task
            task.crontab = monday_8am
            task.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    '✓ Successfully reverted weekly lesson schedule to Monday 8:00 AM'
                )
            )
            
        except PeriodicTask.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    '✗ Task "enqueue-weekly-lesson" not found. Run setup_periodic_tasks first.'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to revert schedule: {e}')
            )