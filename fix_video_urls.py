#!/usr/bin/env python
"""
Fix video URLs to ensure they work with WhiteNoise static file serving
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from apps.workouts.models import VideoClip


def fix_video_urls():
    """Update video URLs to use correct static file path"""
    print("Fixing video URLs...")
    
    updated = 0
    for clip in VideoClip.objects.all():
        old_url = clip.url
        
        # Ensure URL starts with /static/
        if not clip.url.startswith('/static/') and not clip.url.startswith('http'):
            if clip.url.startswith('static/'):
                clip.url = '/' + clip.url
            elif clip.url.startswith('/videos/'):
                clip.url = '/static' + clip.url
            elif clip.url.startswith('videos/'):
                clip.url = '/static/' + clip.url
            else:
                # Assume it's a relative path that should be under static/videos/
                clip.url = '/static/videos/' + clip.url.lstrip('/')
            
            if old_url != clip.url:
                clip.save()
                updated += 1
                print(f"Updated: {old_url} -> {clip.url}")
    
    print(f"\nFixed {updated} video URLs")
    
    # Verify some URLs
    print("\nSample video URLs after fix:")
    for clip in VideoClip.objects.filter(is_active=True)[:5]:
        print(f"  {clip.type}: {clip.url}")


def check_static_files():
    """Check if static files are properly collected"""
    print("\nChecking static files configuration...")
    print(f"STATIC_URL: {settings.STATIC_URL}")
    print(f"STATIC_ROOT: {settings.STATIC_ROOT}")
    
    staticfiles_dir = settings.STATIC_ROOT
    if os.path.exists(staticfiles_dir):
        video_count = 0
        for root, dirs, files in os.walk(os.path.join(staticfiles_dir, 'videos')):
            for file in files:
                if file.endswith('.mp4'):
                    video_count += 1
        print(f"Found {video_count} video files in staticfiles directory")
    else:
        print("WARNING: staticfiles directory does not exist!")
        print("Run: python manage.py collectstatic")


if __name__ == '__main__':
    fix_video_urls()
    check_static_files()