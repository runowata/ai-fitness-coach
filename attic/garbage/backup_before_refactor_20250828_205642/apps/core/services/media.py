"""
Media service for handling R2/S3 storage operations
"""
import logging
import os
from typing import Optional

from django.conf import settings
from django.core.cache import cache

from apps.content.path_normalizer import normalize_media_path, normalize_video_path

logger = logging.getLogger(__name__)

# Constants
R2_PUBLIC_BASE = os.getenv('R2_PUBLIC_BASE', '').rstrip('/')
DEFAULT_EXPIRE = int(os.getenv('AWS_QUERYSTRING_EXPIRE', '7200'))  # 2 hours


class MediaService:
    """Service for handling media operations with R2/S3 storage"""
    
    @staticmethod
    def _calculate_cache_ttl(expiry: Optional[int]) -> int:
        """
        Calculate cache TTL with safety margin
        - Takes 5 minutes off expiry time to avoid using expired URLs
        - Caps at 15 minutes to avoid long-lived cache entries
        - Minimum 1 minute cache
        """
        exp = expiry or DEFAULT_EXPIRE
        return max(60, min(900, exp - 300))  # 1-15 min, usually ~10min for 2h expiry
    
    @staticmethod
    def get_signed_url(file_field, expiry: int = None) -> str:
        """
        Get a signed URL for a file field with caching
        
        Args:
            file_field: Django FileField or ImageField
            expiry: URL expiry time in seconds (default from settings)
            
        Returns:
            Signed URL string
        """
        if not file_field:
            return ''
            
        # Handle invalid input types (integers, etc.)
        if not hasattr(file_field, 'name') and not hasattr(file_field, 'url'):
            logger.warning(f"get_signed_url received invalid input: {type(file_field)} - {file_field}")
            return ''
            
        # Include expiry in cache key to handle different TTLs
        cache_key = f'signed_url:{file_field.name}:{expiry or DEFAULT_EXPIRE}'
        
        # Try to get from cache (skip if Django not configured)
        try:
            cached_url = cache.get(cache_key)
            if cached_url:
                return cached_url
        except Exception:
            pass  # Skip caching if Django not properly configured
            
        try:
            # Get signed URL from storage backend
            if hasattr(file_field, 'url'):
                url = file_field.url
                
                # Cache the URL with calculated TTL (skip if Django not configured)
                try:
                    cache_ttl = MediaService._calculate_cache_ttl(expiry)
                    cache.set(cache_key, url, cache_ttl)
                except Exception:
                    pass  # Skip caching if Django not properly configured
                
                return url
        except Exception as e:
            # Enhanced logging for production debugging
            logger.error(
                f"Error generating signed URL: file={getattr(file_field, 'name', 'unknown')}, "
                f"error={e.__class__.__name__}: {e}"
            )
            # Log to Sentry if available
            try:
                import sentry_sdk
                sentry_sdk.capture_exception(e)
            except ImportError:
                pass
            return ''
            
        return ''
    
    @staticmethod
    def get_video_url(clip) -> str:
        """
        Get video URL for a VideoClip using structured R2 paths
        
        Args:
            clip: VideoClip instance
            
        Returns:
            Public URL for video file
        """
        if not clip or not clip.model_name or not clip.r2_kind:
            return ''
        
        try:
            # Generate structured path based on video kind and clip data
            if clip.r2_kind == 'instruction':
                # Check if it's exercise-specific or general instruction
                if clip.exercise:
                    # Exercise instructions: /videos/instructions/{slug}_instruction_{archetype}_{model}.mp4
                    normalized_slug = normalize_media_path(clip.exercise.id)
                    file_path = f"videos/instructions/{normalized_slug}_instruction_{clip.r2_archetype}_{clip.model_name}.mp4"
                else:
                    # General instructions (closing, intro, etc): /videos/instructions/{model}.mp4
                    file_path = f"videos/instructions/{clip.model_name}.mp4"
            elif clip.r2_kind in ['technique', 'mistake']:
                # Exercises: /videos/exercises/{slug}_{kind}_{model}.mp4
                if not clip.exercise:
                    return ''  # Need exercise link
                normalized_slug = normalize_media_path(clip.exercise.id)
                file_path = f"videos/exercises/{normalized_slug}_{clip.r2_kind}_{clip.model_name}.mp4"
            elif clip.r2_kind in ['weekly', 'closing', 'intro']:
                # General videos: /videos/{kind}/{model}.mp4
                file_path = f"videos/{clip.r2_kind}/{clip.model_name}.mp4"
            else:
                # Fallback for other kinds
                file_path = f"videos/{clip.r2_kind}/{clip.model_name}.mp4"
            
            # Normalize the entire path
            file_path = normalize_media_path(file_path)
            
            # Use public CDN URL
            return MediaService.get_public_cdn_url(file_path)
            
        except Exception as e:
            logger.error(f"Error generating video URL for clip {clip.id}: {e}")
            return ''
    
    @staticmethod
    def get_signed_url_from_key(r2_key: str, expiry: int = None) -> str:
        """
        Get a signed URL directly from R2 key/path
        
        Args:
            r2_key: R2 storage key/path
            expiry: URL expiry time in seconds (default from settings)
            
        Returns:
            Signed URL string
        """
        if not r2_key:
            return ''
        
        try:
            # For now, use public CDN if available
            if R2_PUBLIC_BASE:
                normalized_path = normalize_media_path(r2_key.lstrip('/'))
                return f"{R2_PUBLIC_BASE}/{normalized_path}"
            
            # TODO: Implement signed URL generation directly from R2 key
            # This would require initializing boto3 client and calling generate_presigned_url
            logger.warning(f"No R2_PUBLIC_BASE configured for key: {r2_key}")
            return ''
            
        except Exception as e:
            logger.error(f"Error generating signed URL for key {r2_key}: {e}")
            return ''
    
    @staticmethod
    def get_public_cdn_url(file_field_or_name) -> str:
        """
        Get public CDN URL for a file (if R2 public access is configured)
        
        Args:
            file_field_or_name: Django FileField/ImageField or string path
            
        Returns:
            Public CDN URL string
        """
        if not file_field_or_name:
            return ''
        
        # Handle invalid input types (integers, etc.)
        if isinstance(file_field_or_name, (int, float)):
            logger.warning(f"get_public_cdn_url received invalid input: {type(file_field_or_name)} - {file_field_or_name}")
            return ''
        
        # Handle string path
        if isinstance(file_field_or_name, str):
            if R2_PUBLIC_BASE:
                normalized_path = normalize_media_path(file_field_or_name.lstrip('/'))
                return f"{R2_PUBLIC_BASE}/{normalized_path}"
            return ''
            
        # Handle file field
        if R2_PUBLIC_BASE and hasattr(file_field_or_name, 'name'):
            return f"{R2_PUBLIC_BASE}/{file_field_or_name.name}"
            
        # Fallback to signed URL for file fields only
        if hasattr(file_field_or_name, 'url'):
            return MediaService.get_signed_url(file_field_or_name)
            
        return ''
    
    @staticmethod
    def get_archetype_mapped(archetype: str, to_new: bool = True) -> str:
        """
        Map archetype between old and new naming conventions
        
        Args:
            archetype: Current archetype name
            to_new: If True, map old to new. If False, map new to old.
            
        Returns:
            Mapped archetype name
        """
        # Lazy load settings to avoid Django initialization issues in tests
        try:
            aliases = getattr(settings, 'ARCHETYPE_ALIASES', {})
        except:
            aliases = {}
        
        if to_new:
            # Map old to new (bro -> peer)
            return aliases.get(archetype, archetype)
        else:
            # Map new to old (peer -> bro) - for backward compatibility
            reverse_map = {
                'peer': 'bro',
                'professional': 'sergeant',
                'mentor': 'intellectual'
            }
            return reverse_map.get(archetype, archetype)
    
    @staticmethod
    def get_media_path(category: str, filename: str, archetype: str = None) -> str:
        """
        Generate consistent media path based on category
        
        Args:
            category: Media category (videos/exercises, videos/instructions, etc)
            filename: Base filename
            archetype: Optional archetype for archetype-specific content
            
        Returns:
            Full media path string
        """
        if archetype:
            # Map to old archetype for existing files
            old_archetype = MediaService.get_archetype_mapped(archetype, to_new=False)
            return f"{category}/{filename}_{old_archetype}"
        return f"{category}/{filename}"
    
    @staticmethod
    def invalidate_signed_url_cache(file_field):
        """
        Invalidate cached signed URL for a file
        
        Args:
            file_field: Django FileField or ImageField
        """
        if file_field and hasattr(file_field, 'name'):
            cache_key = f'signed_url:{file_field.name}'
            try:
                cache.delete(cache_key)
                logger.info(f"Invalidated cache for {file_field.name}")
            except Exception:
                pass  # Skip caching if Django not properly configured