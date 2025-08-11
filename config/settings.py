"""
Django settings for AI Fitness Coach project.
"""

from pathlib import Path
import os, secrets
from dotenv import load_dotenv
import dj_database_url

# Load environment variables
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
# SECRET_KEY will be set later after validation
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'
ALLOWED_HOSTS = [
    'ai-fitness-coach-ttzf.onrender.com',
    'localhost',
    '127.0.0.1'
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'storages',
    'django_extensions',
    'django_celery_beat',
    
    # Local apps
    'apps.core',
    'apps.users',
    'apps.workouts',
    'apps.onboarding',
    'apps.content',
    'apps.achievements',
    'apps.ai_integration',
    'apps.notifications',
    'apps.analytics',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'apps.core.middleware.DatabaseSetupMiddleware',  # Auto-setup database on first request
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', '')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'ai_fitness_coach')}",
        conn_max_age=600,
        ssl_require=not DEBUG,  # SSL only in production
    )
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Password hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default timezone for users
DEFAULT_USER_TIMEZONE = 'Europe/Zurich'

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# WhiteNoise configuration - moved to STORAGES dict below

# Storage configuration
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Media files
USE_R2_STORAGE = os.getenv('USE_R2_STORAGE', 'False') == 'True'

if USE_R2_STORAGE:
    # Cloudflare R2 Storage Configuration
    AWS_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID', os.getenv('AWS_ACCESS_KEY_ID'))
    AWS_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY', os.getenv('AWS_SECRET_ACCESS_KEY'))
    AWS_STORAGE_BUCKET_NAME = os.getenv('R2_BUCKET', os.getenv('AWS_STORAGE_BUCKET_NAME', 'ai-fitness-media'))
    AWS_S3_ENDPOINT_URL = os.getenv('R2_ENDPOINT', os.getenv('AWS_S3_ENDPOINT_URL'))
    AWS_S3_REGION_NAME = 'auto'  # критично для R2
    AWS_S3_ADDRESSING_STYLE = 'virtual'  # критично для R2
    AWS_S3_SIGNATURE_VERSION = 's3v4'  # критично для R2
    AWS_DEFAULT_ACL = 'private'
    AWS_QUERYSTRING_AUTH = True
    AWS_QUERYSTRING_EXPIRE = int(os.getenv('AWS_QUERYSTRING_EXPIRE', '7200'))  # 2 hours for videos
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    
    # R2 Public URL (if configured)
    R2_PUBLIC_BASE = os.getenv('R2_PUBLIC_BASE', '')
    
    # R2 CDN and signed URL configuration
    R2_CDN_BASE_URL = os.getenv('R2_CDN_BASE_URL', '')
    R2_SIGNED_URLS = os.getenv('R2_SIGNED_URLS', 'False') == 'True'
    R2_SIGNED_URL_TTL = int(os.getenv('R2_SIGNED_URL_TTL', '3600'))  # 1 hour default
    
    # Update STORAGES for R2
    STORAGES['default'] = {
        'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
    }
    
    MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/'

# Cloudflare Stream settings (for future use)
CF_STREAM_HLS_TEMPLATE = os.getenv('CF_STREAM_HLS_TEMPLATE', 'https://videodelivery.net/{playback_id}/manifest/video.m3u8')

if DEBUG or os.getenv('RENDER'):
    # Local media serving (development or Render deployment)
    MEDIA_URL = '/media/'
    # Fix: Use correct path for Render deployment
    if os.getenv('RENDER'):
        MEDIA_ROOT = '/opt/render/project/src/media'
    else:
        MEDIA_ROOT = BASE_DIR / 'media'
else:
    # AWS S3 settings (other production deployments)
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_DEFAULT_ACL = 'public-read'
    
    # Media files storage
    # DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'  # Удалено - конфликт с STORAGES в Django 4.2+
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Security settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Login URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@aifitnesscoach.com')

# AI Integration
AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai')  # 'openai' or 'anthropic'

# OpenAI settings  
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')  # Updated to latest model
OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '4000'))
OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
USE_JSON_MODE = os.getenv('USE_JSON_MODE', 'False') == 'True'

# Video generation flags
STRICT_ALLOWED_ONLY = os.getenv('STRICT_ALLOWED_ONLY', 'False') == 'True'
SHOW_AI_ANALYSIS = os.getenv('SHOW_AI_ANALYSIS', 'True') == 'True'
AI_REPROMPT_MAX_ATTEMPTS = int(os.getenv('AI_REPROMPT_MAX_ATTEMPTS', '2'))
FALLBACK_TO_LEGACY_FLOW = os.getenv('FALLBACK_TO_LEGACY_FLOW', 'False') == 'True'

# Video storage configuration
R2_CDN_BASE_URL = os.getenv('R2_CDN_BASE_URL', '')
R2_PUBLIC_BASE = os.getenv('R2_PUBLIC_BASE', '')  # Public base URL for motivational cards
R2_SIGNED_URLS = os.getenv('R2_SIGNED_URLS', 'False') == 'True'
R2_SIGNED_URL_TTL = int(os.getenv('R2_SIGNED_URL_TTL', '3600'))

# Playlist generation configuration
PLAYLIST_MISTAKE_PROB = float(os.getenv('PLAYLIST_MISTAKE_PROB', '0.30'))
PLAYLIST_FALLBACK_MAX_CANDIDATES = int(os.getenv('PLAYLIST_FALLBACK_MAX_CANDIDATES', '20'))
PLAYLIST_STORAGE_RETRY = int(os.getenv('PLAYLIST_STORAGE_RETRY', '2'))

# Prompts configuration - fixed to v2 only
PROMPTS_PROFILE = 'v2'  # Clean v2 implementation without legacy support

# Archetype mapping for backward compatibility (old -> new only)
# Import archetype configuration from core constants
from apps.core.constants import ARCHETYPE_ALIASES

# Anthropic Claude settings (alternative)
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-opus-20240229')
ANTHROPIC_MAX_TOKENS = int(os.getenv('ANTHROPIC_MAX_TOKENS', '4000'))

# Rate limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_VIEW = 'apps.core.views.ratelimit_exceeded'

# Age verification
MINIMUM_AGE = 18

# Push Notifications
ONESIGNAL_APP_ID = os.getenv('ONESIGNAL_APP_ID', '')
ONESIGNAL_REST_API_KEY = os.getenv('ONESIGNAL_REST_API_KEY', '')
FCM_SERVER_KEY = os.getenv('FCM_SERVER_KEY', '')

# Analytics
AMPLITUDE_API_KEY = os.getenv('AMPLITUDE_API_KEY', '')
AMPLITUDE_BATCH_SIZE = int(os.getenv('AMPLITUDE_BATCH_SIZE', '10'))

# Monitoring & Alerting
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')
SLACK_ALERT_CHANNEL = os.getenv('SLACK_ALERT_CHANNEL', '#alerts')
SLACK_BOT_USERNAME = os.getenv('SLACK_BOT_USERNAME', 'AI-Fitness-Monitor')
REDIS_ALERT_THRESHOLD_MS = float(os.getenv('REDIS_ALERT_THRESHOLD_MS', '100'))
ALERT_COOLDOWN_SECONDS = int(os.getenv('ALERT_COOLDOWN_SECONDS', '300'))  # 5 minutes
APP_VERSION = os.getenv('APP_VERSION', '0.9.0-rc1')

# Metrics and monitoring
PROMETHEUS_METRICS_EXPORT_PORT = 8001
PROMETHEUS_METRICS_EXPORT_ADDRESS = ''
METRICS_BACKEND = os.getenv('METRICS_BACKEND', 'logging' if DEBUG else 'noop')  # 'statsd', 'logging', 'noop'

# Debug toolbar
INTERNAL_IPS = ['127.0.0.1']

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# ─── Static files via WhiteNoise ────────────────────────────────
# STORAGES already defined above
# Allow Render's dynamic hostname
RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME", "")
ALLOWED_HOSTS += [RENDER_HOST] if RENDER_HOST else []
# Robust SECRET_KEY resolution
if not os.getenv("SECRET_KEY"):
    if DEBUG:
        os.environ["SECRET_KEY"] = "dev-" + secrets.token_urlsafe(32)
    else:
        raise RuntimeError("SECRET_KEY env var required in production")
SECRET_KEY = os.environ["SECRET_KEY"]

# Render.com detection
RENDER = os.getenv('RENDER', 'false').lower() == 'true'

# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Celery Beat Schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'enqueue-weekly-lesson': {
        'task': 'apps.workouts.tasks.enqueue_weekly_lesson',
        'schedule': crontab(minute='*/5'),  # TEMP: Every 5 minutes for testing
        # 'schedule': crontab(hour=8, minute=0, day_of_week=1),  # Production: Every Monday at 8:00 AM
    },
    'send-amplitude-events-batch': {
        'task': 'apps.analytics.tasks.batch_send_events_to_amplitude_task',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'calculate-daily-metrics': {
        'task': 'apps.analytics.tasks.calculate_daily_metrics_task',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1:00 AM
    },
    'cleanup-old-analytics': {
        'task': 'apps.analytics.tasks.cleanup_old_analytics_events_task',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Weekly on Sunday at 2:00 AM
    },
    'system-health-monitor': {
        'task': 'apps.core.tasks.system_health_monitor_task',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}