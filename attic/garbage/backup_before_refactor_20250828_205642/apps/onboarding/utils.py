from django.conf import settings
from django.core.files.storage import default_storage


def public_r2_url(path: str) -> str:
    """
    Generate a public R2 URL from a relative path.
    
    Uses R2_PUBLIC_BASE environment variable + path for public assets
    
    Args:
        path: Relative path like "photos/quotes/card_quotes_0170.jpg"
        
    Returns:
        Full public URL or empty string if unavailable
    """
    if not path:
        return ''
    
    # Clean path - remove leading slashes
    clean_path = path.lstrip('/')
    
    # Use R2_PUBLIC_BASE from environment (set in production)
    import os
    r2_public_base = os.environ.get('R2_PUBLIC_BASE', '').rstrip('/')
    
    if r2_public_base:
        return f"{r2_public_base}/{clean_path}"
    
    # Fallback for development: try Django settings
    r2_public_base = getattr(settings, 'R2_PUBLIC_BASE', '').rstrip('/')
    if r2_public_base:
        return f"{r2_public_base}/{clean_path}"
    
    # No public base available - return empty string
    return ''


def extract_path_from_r2_url(url: str) -> str:
    """
    Extract the relative path from a full R2 public URL.
    
    Args:
        url: Full URL like "https://pub-abc123.r2.dev/photos/quotes/card.jpg"
        
    Returns:
        Relative path like "photos/quotes/card.jpg" or empty string if not matching
    """
    if not url or not url.startswith('http'):
        return ''
    
    import re
    # Match pattern: https://pub-{hash}.r2.dev/{path}
    match = re.search(r'https://pub-[a-f0-9]+\.r2\.dev/(.+)', url)
    if match:
        return match.group(1)
    
    return ''