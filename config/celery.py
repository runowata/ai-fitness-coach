import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Проверяем REDIS_URL в production
redis_url = os.getenv('REDIS_URL')
if os.getenv('RENDER'):
    if not redis_url:
        raise ValueError("REDIS_URL environment variable is required in production for background tasks")
else:
    # В разработке используем локальный Redis или предупреждение
    if not redis_url:
        print("WARNING: REDIS_URL не настроен. Используется локальный Redis (redis://localhost:6379/0)")
        redis_url = 'redis://localhost:6379/0'

app = Celery('ai_fitness_coach')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')