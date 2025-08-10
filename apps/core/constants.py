"""
Core constants used across the application
"""

# Archetype mappings used consistently across the app
ARCHETYPE_MAPPING = {
    '111_nastavnik': 'mentor',        # Мудрый наставник
    '222_professional': 'professional',  # Успешный профессионал  
    '333_rovesnik': 'peer'           # Ровесник
}

# Archetype aliases for different contexts
ARCHETYPE_ALIASES = {
    'intellectual': 'mentor',
    'sergeant': 'professional',
    'bro': 'peer'
}

# Valid archetype names
VALID_ARCHETYPES = ['mentor', 'professional', 'peer']

# Default archetype
DEFAULT_ARCHETYPE = 'mentor'