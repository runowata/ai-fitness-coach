"""
WSGI config for AI Fitness Coach project.
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

# Configure WhiteNoise to serve media files in addition to static files
application = WhiteNoise(application)
application.add_files(settings.MEDIA_ROOT, prefix=settings.MEDIA_URL)