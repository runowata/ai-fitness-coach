"""
Playlist builder v2 - Clean implementation for video playlist generation
"""
from typing import Dict, List, Optional
from django.db.models import Q
from apps.workouts.models import VideoClip, Exercise
from apps.core.services.media import MediaService
import logging

logger = logging.getLogger(__name__)

# Порядок попыток подбора (fallback): точный архетип → generic → любой другой
FALLBACK_ARCHETYPES = [None, "mentor", "professional", "peer"]


def _resolve_clip(ex_slug: str, kind: str, archetype: str) -> Optional[VideoClip]:
    """
    Resolve video clip with fallback strategy
    1. Exact archetype match
    2. Generic (no archetype)
    3. Any other archetype
    """
    try:
        ex = Exercise.objects.get(slug=ex_slug)
    except Exercise.DoesNotExist:
        logger.warning(f"Exercise not found: {ex_slug}")
        return None

    # 1) точный архетип
    qs = VideoClip.objects.filter(
        exercise=ex, 
        r2_kind=kind, 
        archetype=archetype, 
        r2_file__isnull=False
    )
    clip = qs.order_by("-is_active", "-created_at").first()
    if clip:
        logger.debug(f"Found exact match for {ex_slug}/{kind}/{archetype}")
        return clip

    # 2) generic (без привязки к архетипу)
    qs = VideoClip.objects.filter(
        exercise=ex, 
        r2_kind=kind, 
        r2_file__isnull=False
    ).filter(
        Q(archetype="") | Q(archetype__isnull=True)
    )
    clip = qs.order_by("-is_active", "-created_at").first()
    if clip:
        logger.debug(f"Found generic clip for {ex_slug}/{kind}")
        return clip

    # 3) другой архетип как крайний фоллбек
    qs = VideoClip.objects.filter(
        exercise=ex, 
        r2_kind=kind, 
        r2_file__isnull=False
    ).exclude(archetype=archetype)
    clip = qs.order_by("-is_active", "-created_at").first()
    if clip:
        logger.debug(f"Using fallback archetype {clip.archetype} for {ex_slug}/{kind}")
    return clip


def build_playlist(plan_json: Dict, archetype: str) -> List[Dict]:
    """
    Build video playlist from workout plan JSON
    
    Args:
        plan_json: V2 schema workout plan
        archetype: User's trainer archetype (mentor/professional/peer)
        
    Returns:
        List of playlist items with signed URLs and metadata
    """
    out: List[Dict] = []
    weeks = plan_json.get("weeks", [])
    
    for w_idx, week in enumerate(weeks, start=1):
        for d_idx, day in enumerate(week.get("days", []), start=1):
            for block in day.get("blocks", []):
                btype = block.get("type")
                
                if btype in ("warmup", "main", "cooldown"):
                    # Process exercise blocks
                    for ex in block.get("exercises", []):
                        slug = ex.get("slug")
                        if not slug:
                            continue
                            
                        # Get instruction video for the exercise
                        clip = _resolve_clip(slug, "instruction", archetype)
                        if clip:
                            # Safe handling of file fields that might be None or invalid
                            signed_url = ""
                            poster_cdn = ""
                            
                            try:
                                if clip.r2_file:
                                    signed_url = MediaService.get_signed_url(clip.r2_file)
                            except (AttributeError, TypeError) as e:
                                logger.warning(f"Invalid r2_file for clip {clip.id}: {e}")
                            
                            try:
                                if clip.exercise and clip.exercise.poster_image:
                                    poster_cdn = MediaService.get_public_cdn_url(clip.exercise.poster_image)
                            except (AttributeError, TypeError) as e:
                                logger.warning(f"Invalid poster_image for exercise {clip.exercise}: {e}")
                            
                            out.append({
                                "week": w_idx,
                                "day": d_idx,
                                "block": btype,
                                "exercise_slug": slug,
                                "exercise_name": ex.get("name", slug),
                                "sets": ex.get("sets"),
                                "reps": ex.get("reps"),
                                "kind": "instruction",
                                "clip_id": clip.id,
                                "signed_url": signed_url,
                                "poster_cdn": poster_cdn,
                                "archetype": clip.archetype or archetype,
                                "duration_seconds": clip.duration_seconds,
                            })
                        
                        # Add technique/mistake videos if available (for UI hints)
                        for aux_kind in ("technique", "mistake"):
                            clip = _resolve_clip(slug, aux_kind, archetype)
                            if clip:
                                # Safe handling of file fields that might be None or invalid
                                signed_url = ""
                                poster_cdn = ""
                                
                                try:
                                    if clip.r2_file:
                                        signed_url = MediaService.get_signed_url(clip.r2_file)
                                except (AttributeError, TypeError) as e:
                                    logger.warning(f"Invalid r2_file for {aux_kind} clip {clip.id}: {e}")
                                
                                try:
                                    if clip.exercise and clip.exercise.poster_image:
                                        poster_cdn = MediaService.get_public_cdn_url(clip.exercise.poster_image)
                                except (AttributeError, TypeError) as e:
                                    logger.warning(f"Invalid poster_image for {aux_kind} exercise {clip.exercise}: {e}")
                                
                                out.append({
                                    "week": w_idx,
                                    "day": d_idx,
                                    "block": f"{btype}_aux",
                                    "exercise_slug": slug,
                                    "exercise_name": ex.get("name", slug),
                                    "kind": aux_kind,
                                    "clip_id": clip.id,
                                    "signed_url": signed_url,
                                    "poster_cdn": poster_cdn,
                                    "archetype": clip.archetype or archetype,
                                    "duration_seconds": clip.duration_seconds,
                                })
                                
                elif btype == "confidence_task":
                    # Confidence tasks don't have videos, just text
                    out.append({
                        "week": w_idx,
                        "day": d_idx,
                        "block": btype,
                        "text": block.get("text", ""),
                        "description": block.get("description", "")
                    })
    
    logger.info(f"Built playlist with {len(out)} items for archetype {archetype}")
    return out


def get_daily_playlist(plan_json: Dict, archetype: str, week: int, day: int) -> List[Dict]:
    """
    Get playlist for a specific day
    
    Args:
        plan_json: V2 schema workout plan
        archetype: User's trainer archetype
        week: Week number (1-based)
        day: Day number (1-based)
        
    Returns:
        Filtered playlist for the specific day
    """
    full_playlist = build_playlist(plan_json, archetype)
    day_items = [
        item for item in full_playlist 
        if item.get("week") == week and item.get("day") == day
    ]
    logger.info(f"Filtered {len(day_items)} items for week {week}, day {day}")
    return day_items