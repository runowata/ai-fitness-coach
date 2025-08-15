"""
Slug utilities for consistent exercise identification
"""
import re
import unicodedata


def slug_from_text(text: str) -> str:
    """
    Convert any text to normalized slug format
    Rules: lowercase, no spaces, only alphanumeric and hyphens
    
    Examples:
        "Push-Ups" -> "push-ups"
        "Жим лёжа" -> "zhim-lezha"
        "Barbell_Squat" -> "barbell-squat"
    """
    # Normalize unicode characters
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    
    # Convert to lowercase and strip
    text = text.lower().strip()
    
    # Remove everything except letters, numbers, spaces, hyphens
    text = re.sub(r"[^\w\s-]", "", text)
    
    # Replace spaces and underscores with hyphens
    text = re.sub(r"[_\s]+", "-", text)
    
    # Remove multiple hyphens
    text = re.sub(r"-{2,}", "-", text)
    
    # Strip hyphens from edges
    return text.strip("-")


def normalize_exercise_slug(exercise_name: str) -> str:
    """
    Specialized normalization for exercise names
    Handles common variations and Russian names
    """
    # Common replacements for exercises
    replacements = {
        "pushups": "push-ups",
        "pushup": "push-ups",
        "push ups": "push-ups",
        "pull ups": "pull-ups",
        "pullups": "pull-ups",
        "pullup": "pull-ups",
        "sit ups": "sit-ups",
        "situps": "sit-ups",
    }
    
    slug = slug_from_text(exercise_name)
    
    # Apply common replacements
    for old, new in replacements.items():
        if slug == old:
            slug = new
            break
    
    return slug