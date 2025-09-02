"""
Centralized archetype normalization and validation utilities
"""
from typing import Optional, Set

# Valid archetype string identifiers
ALLOWED_ARCHETYPES: Set[str] = {'mentor', 'peer', 'professional'}

# Legacy mapping from old codes to current strings
LEGACY_ARCHETYPE_MAPPING = {
    'bro': 'peer',
    'sergeant': 'professional',
    'intellectual': 'mentor',
}

# Mapping from archetype choice IDs to string identifiers
# These IDs come from onboarding form submissions
ARCHETYPE_BY_OPTION_ID = {
    111: 'mentor',        # Wise Mentor archetype
    112: 'professional',  # Pro Coach archetype  
    113: 'peer',         # Best Mate archetype
}

# String codes that might come from various sources
ARCHETYPE_BY_STRING_CODE = {
    '111': 'mentor',
    '112': 'professional', 
    '113': 'peer',
}


def normalize_archetype(value) -> Optional[str]:
    """
    Normalize archetype value from any source to a valid string identifier.
    
    Handles:
    - Already valid strings: 'mentor', 'peer', 'professional' 
    - Legacy strings: 'bro' -> 'peer', 'sergeant' -> 'professional', etc.
    - Numeric option IDs: 111 -> 'mentor', 112 -> 'professional', 113 -> 'peer'
    - String codes: '111' -> 'mentor', '112' -> 'professional', '113' -> 'peer'
    
    Args:
        value: Raw archetype value from any source
        
    Returns:
        Valid archetype string or None if invalid
    """
    if not value:
        return None
    
    # Already a valid string?
    if isinstance(value, str):
        cleaned = value.strip().lower()
        
        # Direct match
        if cleaned in ALLOWED_ARCHETYPES:
            return cleaned
            
        # Legacy mapping
        if cleaned in LEGACY_ARCHETYPE_MAPPING:
            return LEGACY_ARCHETYPE_MAPPING[cleaned]
            
        # String code mapping
        if cleaned in ARCHETYPE_BY_STRING_CODE:
            return ARCHETYPE_BY_STRING_CODE[cleaned]
    
    # Try as numeric ID
    try:
        numeric_id = int(value)
        if numeric_id in ARCHETYPE_BY_OPTION_ID:
            return ARCHETYPE_BY_OPTION_ID[numeric_id]
    except (ValueError, TypeError):
        pass
    
    # Unknown value
    return None


def validate_archetype(value) -> str:
    """
    Normalize and validate archetype, raising error if invalid.
    
    Args:
        value: Raw archetype value
        
    Returns:
        Valid normalized archetype string
        
    Raises:
        ValueError: If archetype cannot be normalized
    """
    normalized = normalize_archetype(value)
    if not normalized:
        raise ValueError(f"Invalid archetype: {value!r}. Must be one of: {sorted(ALLOWED_ARCHETYPES)}")
    return normalized


def get_archetype_display_name(archetype: str) -> str:
    """
    Get human-readable display name for archetype.
    
    Args:
        archetype: Normalized archetype string
        
    Returns:
        Display name for UI
    """
    display_names = {
        'mentor': 'Wise Mentor',
        'professional': 'Pro Coach', 
        'peer': 'Best Mate',
    }
    return display_names.get(archetype, archetype.title())


def get_archetype_description(archetype: str) -> str:
    """
    Get description for archetype.
    
    Args:
        archetype: Normalized archetype string
        
    Returns:
        Description text
    """
    descriptions = {
        'mentor': 'Supportive, experienced guide who provides wisdom and encouragement',
        'professional': 'Direct, no-nonsense trainer focused on results and efficiency',
        'peer': 'Friendly workout buddy who motivates through camaraderie and fun',
    }
    return descriptions.get(archetype, 'Custom archetype')