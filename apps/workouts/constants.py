"""Constants for workouts app"""

from enum import StrEnum


class VideoKind(StrEnum):
    """Centralized video kinds/types"""
    TECHNIQUE = "technique"
    MISTAKE = "mistake" 
    INSTRUCTION = "instruction"
    INTRO = "intro"
    WEEKLY = "weekly"
    CLOSING = "closing"
    REMINDER = "reminder"
    EXPLAIN = "explain"
    
    # New contextual video types based on reference analysis
    CONTEXTUAL_INTRO = "contextual_intro"    # Context-aware introductions  
    CONTEXTUAL_OUTRO = "contextual_outro"    # Context-aware endings
    MID_WORKOUT = "mid_workout"              # Mid-workout motivational clips
    THEME_BASED = "theme_based"              # Weekly theme-based lessons
    MOTIVATIONAL_BREAK = "motivational_break"  # Short motivational breaks

    @classmethod
    def choices(cls):
        """Django choices format"""
        return [(kind.value, kind.value.title()) for kind in cls]


class Archetype(StrEnum):
    """User archetypes for video content"""
    PEER = "peer"
    PROFESSIONAL = "professional" 
    MENTOR = "mentor"
    
    # Legacy mapping for backwards compatibility
    BRO = "peer"  # Maps to peer
    SERGEANT = "professional"  # Maps to professional  
    INTELLECTUAL = "mentor"  # Maps to mentor

    @classmethod
    def choices(cls):
        """Django choices format"""
        return [
            (cls.PEER.value, 'Ровесник'),
            (cls.PROFESSIONAL.value, 'Успешный профессионал'),
            (cls.MENTOR.value, 'Мудрый наставник'),
        ]

    @classmethod
    def normalize(cls, archetype: str) -> str:
        """Normalize legacy archetypes to current ones"""
        mapping = {
            'bro': cls.PEER.value,
            'sergeant': cls.PROFESSIONAL.value, 
            'intellectual': cls.MENTOR.value,
        }
        return mapping.get(archetype, archetype)


# Required video kinds for exercise validation  
# Note: INSTRUCTION videos are general/archetype-specific, not exercise-specific
# Only TECHNIQUE and MISTAKE are required per exercise
REQUIRED_VIDEO_KINDS = [VideoKind.TECHNIQUE, VideoKind.MISTAKE]

# Exercise fallback priority for substitutions
EXERCISE_FALLBACK_PRIORITY = {
    "muscle_group": 1,  # First by muscle group
    "equipment": 2,     # Then by equipment
    "difficulty": 3,    # Then by difficulty
}

# Archetype fallback order for video selection
ARCHETYPE_FALLBACK_ORDER = {
    "professional": ["professional", "mentor", "peer"],
    "mentor": ["mentor", "professional", "peer"],
    "peer": ["peer", "professional", "mentor"],
}

# Playlist generation constants
PLAYLIST_FALLBACK_MAX_CANDIDATES = 20  # Max candidates per fallback level
PLAYLIST_STORAGE_RETRY = 2             # Storage availability retry attempts
PLAYLIST_MISTAKE_PROB = 0.30           # Probability to include mistake videos

# Required vs optional video kinds for fallback strategy
REQUIRED_VIDEO_KINDS_PLAYLIST = [VideoKind.TECHNIQUE, VideoKind.INSTRUCTION]
OPTIONAL_VIDEO_KINDS_PLAYLIST = [
    VideoKind.MISTAKE, VideoKind.INTRO, VideoKind.WEEKLY, VideoKind.CLOSING,
    VideoKind.CONTEXTUAL_INTRO, VideoKind.CONTEXTUAL_OUTRO, VideoKind.MID_WORKOUT,
    VideoKind.THEME_BASED, VideoKind.MOTIVATIONAL_BREAK, VideoKind.REMINDER
]

# Contextual playlist generation settings
CONTEXTUAL_INTRO_SELECTION_FACTORS = [
    'week_context',     # Week number in course
    'mood_type',        # User/system mood
    'content_theme',    # Thematic context
]

MID_WORKOUT_INSERTION_FREQUENCY = 3  # Every 3rd exercise gets mid-workout motivation
WEEKLY_THEME_VIDEO_PRIORITY = 1      # High priority for theme-based videos