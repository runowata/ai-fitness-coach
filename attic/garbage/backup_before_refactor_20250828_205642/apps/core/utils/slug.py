"""
Slug normalization utilities for consistent exercise identification
"""
import re
import unicodedata
from typing import Dict


# Compiled regex patterns for performance
_SLUG_RE = re.compile(r'[^a-z0-9-]+')
_DASH_RE = re.compile(r'-{2,}')


def slugify_strict(text: str) -> str:
    """
    Strict slug normalization based on GPT recommendations.
    Creates canonical slugs: only a-z, 0-9, - (ASCII), lowercase.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized slug string
    """
    if not text:
        return ""
    
    # Normalize Unicode characters
    text = unicodedata.normalize('NFKD', text)
    
    # Convert to ASCII, removing non-ASCII characters
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Convert to lowercase and strip whitespace
    text = text.lower().strip()
    
    # Replace underscores and spaces with hyphens
    text = text.replace('_', '-').replace(' ', '-')
    
    # Remove all non-alphanumeric except hyphens
    text = _SLUG_RE.sub('-', text)
    
    # Collapse multiple hyphens into single hyphen
    text = _DASH_RE.sub('-', text)
    
    # Remove leading/trailing hyphens
    return text.strip('-')


def slug_from_text(text: str) -> str:
    """
    Legacy compatibility wrapper for slugify_strict
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized slug string
    """
    return slugify_strict(text)


# Slug aliases dictionary for AI response variations
SLUG_ALIASES: Dict[str, str] = {
    # Common AI variations
    "pushups": "push-up",
    "push_ups": "push-up", 
    "push-ups": "push-up",
    "air-squats": "squat",
    "air_squats": "squat",
    "bodyweight-squats": "squat",
    "bodyweight_squats": "squat",
    "jumping-jacks": "jumping-jack",
    "jumping_jacks": "jumping-jack",
    "mountain-climbers": "mountain-climber",
    "mountain_climbers": "mountain-climber",
    "sit-ups": "sit-up",
    "sit_ups": "sit-up",
    "crunches": "crunch",
    "planks": "plank",
    "lunges": "lunge",
    "burpees": "burpee",
    
    # Exercise ID format variations (EX027_v2 style)
    "ex027-v2": "EX027_v2",
    "ex-027-v2": "EX027_v2",
    "ex027v2": "EX027_v2",
    
    # Common typos and variations
    "pushup": "push-up",
    "pullup": "pull-up",
    "pullups": "pull-up",
    "pull_up": "pull-up",
    "pull-ups": "pull-up",
    "deadlift": "dead-lift",
    "deadlifts": "dead-lift",
    "bicep-curl": "bicep-curls",
    "bicep_curl": "bicep-curls",
}


def normalize_exercise_slug(exercise_name: str) -> str:
    """
    Normalize exercise slug with alias mapping
    
    Args:
        exercise_name: Exercise name or ID to normalize
        
    Returns:
        Normalized slug
    """
    if not exercise_name:
        return ""
    
    # First normalize the slug
    normalized = slugify_strict(exercise_name)
    
    # Check if we have an alias for this variation
    return SLUG_ALIASES.get(normalized, normalized)


def normalize_slug_with_aliases(slug: str) -> str:
    """
    Normalize slug with fallback to aliases dictionary.
    Safety net for AI response variations.
    
    Args:
        slug: Input slug to normalize
        
    Returns:
        Normalized slug, mapped through aliases if available
    """
    return normalize_exercise_slug(slug)