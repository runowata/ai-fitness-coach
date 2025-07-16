"""
Django settings for AI Fitness Coach project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# Load environment variables
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if os.getenv('RENDER'):
        raise ValueError("SECRET_KEY environment variable is required in production")
    else:
        SECRET_KEY = 'django-insecure-dev-key-change-in-production'

DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() in ('1', 'true', 'yes', 'on')
# Dynamic ALLOWED_HOSTS (можно переопределить через переменную окружения)
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') if os.getenv('DJANGO_ALLOWED_HOSTS') else [
    'ai-fitness-coach-ttzf.onrender.com',
    'ai-fitness-web.onrender.com',  # новый домен для веб-сервиса
    '.onrender.com',  # все поддомены Render
    'localhost',
    '127.0.0.1',
    'testserver'  # For Django tests
]

# CSRF trusted origins for frontend on different domains
CSRF_TRUSTED_ORIGINS = os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS') else [
    'https://ai-fitness-coach-ttzf.onrender.com',
    'https://ai-fitness-web.onrender.com',
]

# Security settings for production
if os.getenv('RENDER'):
    # SSL/HTTPS settings - proper configuration for Render
    SECURE_SSL_REDIRECT = True  # Works correctly with SECURE_PROXY_SSL_HEADER
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Cookie security
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    
    # Additional security headers
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Secure proxy headers for Render (critical for SSL redirect to work)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Additional proxy settings for Render
    USE_X_FORWARDED_HOST = True
    SECURE_REDIRECT_EXEMPT = [r"^health/?$"]  # Health check endpoint
else:
    # Development settings
    SECURE_SSL_REDIRECT = False
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False

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
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
if os.getenv('REDIS_URL'):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.getenv('REDIS_URL'),
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'))
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_WORKER_CONCURRENCY = int(os.getenv('CELERY_WORKER_CONCURRENCY', '2'))
CELERY_TASK_TIME_LIMIT = int(os.getenv('CELERY_TASK_TIME_LIMIT', '300'))  # 5 minutes
CELERY_WORKER_PREFETCH_MULTIPLIER = int(os.getenv('CELERY_WORKER_PREFETCH_MULTIPLIER', '1'))
CELERY_TASK_ALWAYS_EAGER = os.getenv('CELERY_TASK_ALWAYS_EAGER', 'False') == 'True'

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

# Password hashing - use reliable hashers
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
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

# WhiteNoise configuration - use simple storage without manifest
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
WHITENOISE_USE_FINDERS = True
WHITENOISE_MAX_AGE = 31536000  # 1 year cache for static files
WHITENOISE_MANIFEST_STRICT = False  # Allow missing files
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['mp4', 'mov', 'avi', 'webm']  # Don't compress videos
WHITENOISE_MIMETYPES = {
    '.mp4': 'video/mp4',
    '.mov': 'video/quicktime',
    '.avi': 'video/x-msvideo',
    '.webm': 'video/webm',
}

# Media files
USE_S3 = os.getenv('USE_S3', 'False') == 'True'

if USE_S3:
    # AWS S3 settings for production deployments with S3
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
    
    # Validate required S3 settings
    if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME]):
        raise ValueError("USE_S3=True requires AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_STORAGE_BUCKET_NAME")
    
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = False
    
    # Media files storage
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
else:
    # Local media storage (development and Render)
    MEDIA_URL = '/media/'
    if os.getenv('RENDER'):
        # Render Disk mounted at /opt/render/project/src/media
        MEDIA_ROOT = '/opt/render/project/src/media'
    else:
        MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Use database for sessions
SESSION_COOKIE_AGE = 86400 * 30  # 30 days
SESSION_COOKIE_NAME = 'sessionid'
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Security settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Login URLs
LOGIN_URL = '/users/login/'  # Proper login page for unauthenticated users
LOGIN_REDIRECT_URL = '/users/dashboard/'  # After login, go to dashboard
LOGOUT_REDIRECT_URL = '/'  # After logout, go to home

# Email settings
if os.getenv('RENDER') and os.getenv('EMAIL_HOST_USER') and os.getenv('EMAIL_HOST_PASSWORD'):
    # Production email settings (only if credentials are provided)
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@aifitnesscoach.com')
    SERVER_EMAIL = DEFAULT_FROM_EMAIL
    EMAIL_TIMEOUT = 60
else:
    # Console backend for development or when email credentials are not set
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'noreply@aifitnesscoach.com'

# AI Integration
AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai')  # 'openai' or 'anthropic'

# OpenAI settings
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY and os.getenv('RENDER'):
    raise ValueError("OPENAI_API_KEY environment variable is required in production")

OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '4000'))
OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))

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

# Metrics and monitoring
PROMETHEUS_METRICS_EXPORT_PORT = 8001
PROMETHEUS_METRICS_EXPORT_ADDRESS = ''

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