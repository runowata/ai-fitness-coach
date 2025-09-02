"""
Test settings - disable cache and external dependencies
Extended for CSV import testing with SQLite
"""

# Import main settings as base
from .settings import *

# Override with test-specific settings
SECRET_KEY = 'test-key-for-csv-import-testing-12345'
DEBUG = True

# Disable cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable Celery for tests  
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Test database - use file instead of memory for CSV import testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test_csv_import.sqlite3',  # File DB for persistence during testing
    }
}

# Test-friendly settings
METRICS_BACKEND = 'logging'
SHOW_AI_ANALYSIS = True
AI_REPROMPT_MAX_ATTEMPTS = 1
FALLBACK_TO_LEGACY_FLOW = False

# Playlist settings for deterministic tests
PLAYLIST_MISTAKE_PROB = 0.5
PLAYLIST_FALLBACK_MAX_CANDIDATES = 10
PLAYLIST_STORAGE_RETRY = 2

# Disable external services
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

# Logging for tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}