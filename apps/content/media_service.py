"""
Media service for handling file URLs and storage operations.
Provides a unified interface for media URLs regardless of storage backend.
"""

from django.core.files.storage import default_storage


def public_url(path: str) -> str:
    """
    Get public URL for a media file path.
    
    Args:
        path: File path relative to media root (e.g., 'videos/exercise.mp4')
        
    Returns:
        Full public URL for the file
    """
    if not path:
        return ''
    
    # Ensure path doesn't start with slash for consistency
    clean_path = path.lstrip('/')
    
    return default_storage.url(clean_path)


def poster_url(path: str) -> str:
    """
    Get poster/thumbnail URL for a media file.
    Currently just wraps public_url but can be extended for poster-specific logic.
    
    Args:
        path: File path relative to media root
        
    Returns:
        Full public URL for the poster/thumbnail
    """
    return public_url(path)


def get_video_url(video_path: str) -> str:
    """
    Get video URL with proper handling.
    
    Args:
        video_path: Video file path
        
    Returns:
        Full public URL for the video
    """
    return public_url(video_path)


def get_image_url(image_path: str) -> str:
    """
    Get image URL with proper handling.
    
    Args:
        image_path: Image file path
        
    Returns:
        Full public URL for the image
    """
    return public_url(image_path)


def get_media_url(media_path: str) -> str:
    """
    Generic media URL getter.
    
    Args:
        media_path: Media file path
        
    Returns:
        Full public URL for the media file
    """
    return public_url(media_path)