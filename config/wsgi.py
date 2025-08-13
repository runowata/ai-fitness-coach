"""
WSGI config for AI Fitness Coach project.
"""

import os

from django.conf import settings
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

# Configure WhiteNoise to serve media files in addition to static files
application = WhiteNoise(application)

# Only serve local media files if R2 storage is not enabled
if not getattr(settings, "USE_R2_STORAGE", False) and getattr(settings, "MEDIA_ROOT", None) and getattr(settings, "MEDIA_URL", None):
    application.add_files(settings.MEDIA_ROOT, prefix=settings.MEDIA_URL)