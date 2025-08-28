from django.core.management.base import BaseCommand
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Debug storage configuration for troubleshooting motivational cards'

    def handle(self, *args, **options):
        self.stdout.write("=== Storage Configuration Debug ===")
        
        # Environment variables
        self.stdout.write(f"USE_R2_STORAGE: {os.getenv('USE_R2_STORAGE', 'Not set')}")
        self.stdout.write(f"USE_S3: {os.getenv('USE_S3', 'Not set')}")
        self.stdout.write(f"R2_PUBLIC_BASE: {os.getenv('R2_PUBLIC_BASE', 'Not set')}")
        self.stdout.write(f"AWS_ACCESS_KEY_ID: {'Set' if os.getenv('AWS_ACCESS_KEY_ID') else 'Not set'}")
        
        # Settings values
        use_r2 = getattr(settings, 'USE_R2_STORAGE', False)
        self.stdout.write(f"Settings USE_R2_STORAGE: {use_r2}")
        
        # Storage backend
        if hasattr(settings, 'STORAGES'):
            default_storage_backend = settings.STORAGES.get('default', {}).get('BACKEND', 'Not set')
            self.stdout.write(f"Default storage backend: {default_storage_backend}")
        
        # Test URL generation
        self.stdout.write("\n=== Testing URL Generation ===")
        
        from django.core.files.storage import default_storage
        test_file = "photos/quotes/card_quotes_0001.jpg"
        
        try:
            test_url = default_storage.url(test_file)
            self.stdout.write(f"Test URL for {test_file}: {test_url}")
            
            if test_url.startswith('/media/'):
                self.stdout.write("→ Local development URL (will show fallback)")
            elif test_url.startswith('https://'):
                self.stdout.write("→ R2 signed URL (should show image)")
            else:
                self.stdout.write("→ Unknown URL format")
                
        except Exception as e:
            self.stdout.write(f"Error generating URL: {e}")
        
        # Test motivational background function
        self.stdout.write("\n=== Testing Motivational Background Function ===")
        
        try:
            from apps.onboarding.views import _get_random_motivational_background
            bg_url = _get_random_motivational_background()
            self.stdout.write(f"Background URL: '{bg_url}'")
            
            if bg_url == '':
                self.stdout.write("→ Empty URL (will show gradient + fallback)")
            else:
                self.stdout.write(f"→ Generated URL: {bg_url}")
                
        except Exception as e:
            self.stdout.write(f"Error in background function: {e}")
        
        self.stdout.write("\n=== Recommendations ===")
        if not use_r2:
            self.stdout.write("❌ USE_R2_STORAGE is False - images will not load from R2")
            self.stdout.write("✅ Fallback icons should be displayed instead")
        else:
            self.stdout.write("✅ USE_R2_STORAGE is True - should generate signed URLs")