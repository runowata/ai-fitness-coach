#!/usr/bin/env python
"""Test media proxy locally"""

import os
import sys
import django

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_sqlite')
django.setup()

from django.test import RequestFactory
from apps.content.views import media_proxy

# Test with mock R2 credentials (they won't work but should show the flow)
os.environ.update({
    'AWS_STORAGE_BUCKET_NAME': 'ai-fitness-media',
    'AWS_S3_ENDPOINT_URL': 'https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com',
    'AWS_ACCESS_KEY_ID': 'test_key',
    'AWS_SECRET_ACCESS_KEY': 'test_secret',
    'R2_SIGNED_URL_TTL': '3600'
})

factory = RequestFactory()
request = factory.get('/content/media/images/avatars/peer_avatar_1.jpg')

try:
    response = media_proxy(request, 'images/avatars/peer_avatar_1.jpg')
    print(f"✅ Media proxy works! Status: {response.status_code}")
    if hasattr(response, 'url'):
        print(f"Redirect URL: {response.url}")
    elif 'Location' in response:
        print(f"Redirect URL: {response['Location']}")
except Exception as e:
    if "InvalidAccessKeyId" in str(e) or "InvalidSecretAccessKey" in str(e):
        print("✅ Media proxy logic works! (Invalid credentials expected)")
        print(f"Error: {e}")
    else:
        print(f"❌ Unexpected error: {e}")