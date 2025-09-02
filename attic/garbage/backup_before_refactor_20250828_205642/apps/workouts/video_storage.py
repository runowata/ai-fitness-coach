"""Video storage abstraction layer for multiple providers"""

from typing import TYPE_CHECKING, Protocol

from django.conf import settings
from django.core.files.storage import default_storage

from .models import VideoProvider

if TYPE_CHECKING:
    from .models import VideoClip


class VideoStorage(Protocol):
    """Protocol for video storage adapters"""
    
    def exists(self, clip: 'VideoClip') -> bool:
        """Check if video exists in storage"""
        ...
    
    def playback_url(self, clip: 'VideoClip') -> str:
        """Get playback URL for video"""
        ...


class R2Adapter:
    """Cloudflare R2 storage adapter with CDN and signed URL support"""
    
    def exists(self, clip: 'VideoClip') -> bool:
        """Check if R2 video file exists"""
        if not clip.model_name or not clip.r2_kind:
            return False
        # Trust DB for performance - could add storage.exists() check if needed
        return True
    
    def playback_url(self, clip: 'VideoClip') -> str:
        """Get R2 video playback URL using structured paths"""
        from apps.core.services.media import MediaService
        
        # Use structured path URL generation
        return MediaService.get_video_url(clip)
    
    def _generate_signed_url(self, file_field) -> str:
        """Generate signed URL for private R2 bucket access"""
        try:
            # Check if storage supports signed URLs (S3Boto3Storage)
            if hasattr(default_storage, 'connection'):
                client = default_storage.connection.meta.client
                ttl = getattr(settings, 'R2_SIGNED_URL_TTL', 3600)  # 1 hour default
                
                url = client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': default_storage.bucket_name,
                        'Key': file_field.name
                    },
                    ExpiresIn=ttl
                )
                return url
            else:
                # Fallback to regular URL if signed URLs not supported
                return default_storage.url(file_field.name)
        except Exception:
            # Fallback on any error
            return default_storage.url(file_field.name)


class StreamAdapter:
    """Cloudflare Stream adapter"""
    
    def exists(self, clip: 'VideoClip') -> bool:
        """Check if Stream video exists"""
        return bool(clip.stream_uid or clip.playback_id)
    
    def playback_url(self, clip: 'VideoClip') -> str:
        """Get Stream HLS playback URL"""
        if not (clip.stream_uid or clip.playback_id):
            return ''
        
        # Get template from settings - don't hardcode domain
        template = getattr(settings, 'CF_STREAM_HLS_TEMPLATE', 
                          'https://videodelivery.net/{playback_id}/manifest/video.m3u8')
        
        playback_id = clip.playback_id or clip.stream_uid
        return template.format(playback_id=playback_id)


class ExternalAdapter:
    """External URL adapter (for future use)"""
    
    def exists(self, clip: 'VideoClip') -> bool:
        """Check if external URL is available"""
        # Future: check external_url field
        return False
    
    def playback_url(self, clip: 'VideoClip') -> str:
        """Get external URL"""
        # Future: return clip.external_url
        return ''


def get_storage(clip: 'VideoClip') -> VideoStorage:
    """Factory function to get appropriate storage adapter"""
    if clip.provider == VideoProvider.R2:
        return R2Adapter()
    elif clip.provider == VideoProvider.STREAM:
        return StreamAdapter()
    elif clip.provider == VideoProvider.EXTERNAL:
        return ExternalAdapter()
    else:
        # Default fallback to R2
        return R2Adapter()