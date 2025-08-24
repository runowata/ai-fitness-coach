"""
Media path normalization service for AI Fitness Coach.

This module provides functions to normalize media file paths to ensure consistent
mapping between database entries and actual R2/S3 storage paths.
"""

import re


def normalize_media_path(path: str) -> str:
    """
    Normalize media path according to known mapping rules.
    
    Common normalization patterns:
    - pushups_technique_mod1 → push_ups_technique_m01
    - card_motivation_1 → card_quotes_0001 (pad to 4 digits)
    - Hyphens to underscores for consistency
    
    Args:
        path: Original media path
        
    Returns:
        Normalized media path
    """
    if not path:
        return path
        
    normalized = path
    
    # Rule 1: pushups_technique_mod(\d) → push_ups_technique_m0\1
    # Handle pushups variations
    normalized = re.sub(
        r'pushups_technique_mod(\d)',
        r'push_ups_technique_m0\1',
        normalized
    )
    
    # Rule 2: card_motivation_(\d+) → card_quotes_000\1 (pad to 4 digits)
    def pad_card_number(match):
        number = match.group(1)
        padded_number = number.zfill(4)
        return f'card_quotes_{padded_number}'
    
    normalized = re.sub(
        r'card_motivation_(\d+)',
        pad_card_number,
        normalized
    )
    
    # Rule 3: Normalize hyphens to underscores for consistency
    normalized = normalized.replace('-', '_')
    
    # Rule 4: Handle common exercise name variations
    exercise_mappings = {
        'pushups': 'push_ups',
        'pullups': 'pull_ups',
        'situps': 'sit_ups',
        'standup': 'stand_up',
        'warmup': 'warm_up',
        'cooldown': 'cool_down',
    }
    
    for old_name, new_name in exercise_mappings.items():
        normalized = normalized.replace(old_name, new_name)
    
    return normalized


def normalize_video_path(exercise_slug: str, video_type: str, archetype: str = None, model: str = "m01") -> str:
    """
    Generate normalized video path for exercises.
    
    Args:
        exercise_slug: Exercise slug (e.g., "push_ups")
        video_type: Type of video ("technique", "mistake", "instruction", "reminder")
        archetype: Archetype code for instruction/reminder videos ("mentor", "professional", "peer")
        model: Model identifier (default: "m01")
        
    Returns:
        Normalized video path
    """
    base_slug = normalize_media_path(exercise_slug)
    
    if video_type in ["technique", "mistake"]:
        return f"videos/exercises/{base_slug}_{video_type}_{model}.mp4"
    elif video_type == "instruction" and archetype:
        return f"videos/instructions/{base_slug}_instruction_{archetype}_{model}.mp4"
    elif video_type == "reminder" and archetype:
        # For reminders, we might have numbered variations
        return f"videos/reminders/{base_slug}_reminder_{archetype}_1.mp4"
    else:
        # Default fallback
        return f"videos/exercises/{base_slug}_{video_type}_{model}.mp4"


def normalize_image_path(image_type: str, category: str = None, number: int = 1) -> str:
    """
    Generate normalized image path.
    
    Args:
        image_type: Type of image ("card", "avatar")
        category: Category for cards ("quotes", "motivation") or archetype for avatars
        number: Image number
        
    Returns:
        Normalized image path
    """
    if image_type == "card" and category:
        padded_number = str(number).zfill(4)
        normalized_category = normalize_media_path(category)
        return f"images/cards/card_{normalized_category}_{padded_number}.jpg"
    elif image_type == "avatar" and category:
        normalized_archetype = normalize_media_path(category)
        return f"images/avatars/{normalized_archetype}_avatar_{number}.jpg"
    else:
        return f"images/{image_type}_{number}.jpg"


def get_media_url_variants(base_path: str) -> list[str]:
    """
    Get common variants of a media path for fallback purposes.
    
    Args:
        base_path: Base media path
        
    Returns:
        List of path variants to try
    """
    variants = [base_path]
    
    # Add normalized version
    normalized = normalize_media_path(base_path)
    if normalized != base_path:
        variants.append(normalized)
    
    # Add common variations
    if 'push_ups' in base_path:
        variants.append(base_path.replace('push_ups', 'pushups'))
    if 'pushups' in base_path:
        variants.append(base_path.replace('pushups', 'push_ups'))
        
    # Add hyphen/underscore variants
    if '_' in base_path:
        variants.append(base_path.replace('_', '-'))
    if '-' in base_path:
        variants.append(base_path.replace('-', '_'))
    
    return list(set(variants))  # Remove duplicates