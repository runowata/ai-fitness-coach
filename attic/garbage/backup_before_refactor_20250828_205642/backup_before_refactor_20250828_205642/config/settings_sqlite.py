"""
SQLite settings for local migrations and testing without remote DB connection
"""

from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'dev.sqlite3',
    }
}

# Disable automatic migration middleware
ENABLE_DB_SETUP_MW = False

# Disable cache for local testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}