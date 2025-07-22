from whitenoise.middleware import WhiteNoiseMiddleware
from django.conf import settings


class WhiteNoiseExcludeMediaMiddleware(WhiteNoiseMiddleware):
    """
    Custom WhiteNoise middleware that excludes media files from being handled
    by WhiteNoise, allowing Django's media serving to work properly.
    """
    
    def should_handle(self, path, method):
        """
        Override to skip media files and let Django handle them.
        """
        # Пропускаем /media/** дальше в Django
        if path.startswith(settings.MEDIA_URL.lstrip('/')):
            return False
        return super().should_handle(path, method)