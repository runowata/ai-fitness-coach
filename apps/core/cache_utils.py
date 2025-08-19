from django.core.cache import cache

def cache_safe_get(key, default=None):
    """
    Safely get value from cache.
    Returns default if cache is unavailable.
    """
    try:
        return cache.get(key, default)
    except Exception:
        return default

def cache_safe_set(key, value, timeout=None):
    """
    Safely set value in cache.
    Returns True if successful, False if cache is unavailable.
    """
    try:
        cache.set(key, value, timeout)
        return True
    except Exception:
        return False

def cache_safe_delete(key):
    """
    Safely delete key from cache.
    Returns True if successful, False if cache is unavailable.
    """
    try:
        cache.delete(key)
        return True
    except Exception:
        return False