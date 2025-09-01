"""
Playlist builder v2 - Clean implementation for video playlist generation
"""
import logging
from typing import Dict, List, Optional, Set
from django.conf import settings

from django.db.models import Q

from apps.core.services.media import MediaService
from apps.workouts.models import CSVExercise, R2Video

logger = logging.getLogger(__name__)

# Порядок попыток подбора (fallback): точный архетип → generic → любой другой
FALLBACK_ARCHETYPES = [None, "mentor", "professional", "peer"]


class StrictPlaylistValidator:
    """
    Строгая валидация плейлистов с поддержкой fallback режима
    
    В обычном режиме - позволяет fallback'и и выдает предупреждения
    В строгом режиме - падает при отсутствии обязательных элементов
    """
    
    def __init__(self, strict_mode: bool = None):
        if strict_mode is None:
            strict_mode = getattr(settings, 'PLAYLIST_STRICT_MODE', False)
        self.strict_mode = strict_mode
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_exercise_exists(self, ex_slug: str) -> bool:
        """
        Проверка существования упражнения в базе данных
        
        Args:
            ex_slug: ID упражнения
            
        Returns:
            bool: True если упражнение найдено
            
        Raises:
            ValueError: В строгом режиме при отсутствии упражнения
        """
        if not ex_slug:
            error_msg = "EXERCISE_SLUG_EMPTY"
            if self.strict_mode:
                raise ValueError(error_msg)
            self.validation_warnings.append(error_msg)
            return False
        
        exists = CSVExercise.objects.filter(id=ex_slug, is_active=True).exists()
        
        if not exists:
            error_msg = f"EXERCISE_SLUG_UNKNOWN: '{ex_slug}'"
            if self.strict_mode:
                raise ValueError(error_msg)
            self.validation_warnings.append(error_msg)
            return False
            
        return True
    
    def validate_video_availability(self, ex_slug: str, kind: str, archetype: str) -> bool:
        """
        Проверка доступности видео для упражнения
        
        Args:
            ex_slug: ID упражнения
            kind: Тип видео (instruction, technique, mistake)
            archetype: Архетип тренера
            
        Returns:
            bool: True если видео найдено
            
        Raises:
            ValueError: В строгом режиме при отсутствии критичного видео
        """
        clip = _resolve_clip(ex_slug, kind, archetype)
        
        if not clip:
            error_msg = f"VIDEO_MISSING: {ex_slug}/{kind}/{archetype}"
            # Критичные видео (instruction) обязательны в строгом режиме
            if self.strict_mode and kind == "instruction":
                raise ValueError(error_msg)
            if kind == "instruction":
                self.validation_warnings.append(error_msg)
            return False
            
        # Проверка что у R2Video есть реальный файл
        # R2Video всегда имеет файл, так как создается только для существующих файлов в R2
        # Проверка опциональна через настройки
        fail_on_missing = getattr(settings, 'PLAYLIST_FAIL_ON_MISSING_VIDEOS', False)
        if fail_on_missing and not clip.r2_url:
            error_msg = f"VIDEO_FILE_MISSING: {ex_slug}/{kind}/{archetype} (clip_id: {clip.code})"
            if self.strict_mode:
                raise ValueError(error_msg)
            self.validation_warnings.append(error_msg)
            return False
            
        return True
    
    def validate_playlist_completeness(self, playlist: List[Dict], is_rest_day: bool = False) -> bool:
        """
        Проверка полноты плейлиста на наличие обязательных сегментов
        
        Args:
            playlist: Список элементов плейлиста
            is_rest_day: Флаг дня отдыха
            
        Returns:
            bool: True если плейлист полный
            
        Raises:
            ValueError: В строгом режиме при неполном плейлисте
        """
        if not self.strict_mode:
            return True
            
        # Собираем типы элементов в плейлисте
        playlist_types: Set[str] = set()
        for item in playlist:
            item_type = item.get('type') or item.get('block', '')
            playlist_types.add(item_type)
        
        # Обязательные сегменты для обычного дня
        required_types = set()
        if not is_rest_day:
            # Для тренировочных дней нужны инструкции к упражнениям
            has_instructions = any(
                item.get('kind') == 'instruction' 
                for item in playlist 
                if item.get('kind')
            )
            if not has_instructions:
                required_types.add('instruction')
        
        # Проверка недостающих типов
        missing_types = required_types - playlist_types
        if missing_types:
            error_msg = f"PLAYLIST_INCOMPLETE: Missing segments: {missing_types}"
            if self.strict_mode:
                raise ValueError(error_msg)
            self.validation_warnings.append(error_msg)
            return False
            
        return True
    
    def get_validation_report(self) -> Dict[str, List[str]]:
        """
        Получить отчет о валидации
        
        Returns:
            Dict с ошибками и предупреждениями
        """
        return {
            'errors': self.validation_errors,
            'warnings': self.validation_warnings
        }


def _resolve_clip(ex_slug: str, kind: str, archetype: str) -> Optional[R2Video]:
    """
    Resolve video clip with fallback strategy
    1. Exact archetype match
    2. Generic (no archetype)
    3. Any other archetype
    """
    try:
        ex = CSVExercise.objects.get(id=ex_slug)
    except CSVExercise.DoesNotExist:
        logger.warning(f"Exercise not found: {ex_slug}")
        return None

    # 1) точный архетип - ищем R2Video с соответствующими параметрами
    # Для R2Video код = имя файла, архетип и тип определяются из naming convention
    code_pattern = f"{ex_slug}_{kind}_{archetype}"
    qs = R2Video.objects.filter(
        code__icontains=code_pattern,
        category='exercises',
        archetype=archetype
    )
    clip = qs.order_by("-is_active", "-created_at").first()
    if clip:
        logger.debug(f"Found exact R2Video match for {ex_slug}/{kind}/{archetype}")
        return clip

    # 2) generic (без привязки к архетипу)
    # Ищем видео для упражнения без конкретного архетипа
    code_pattern = f"{ex_slug}_{kind}"
    qs = R2Video.objects.filter(
        code__icontains=code_pattern,
        category='exercises'
    ).filter(
        Q(archetype="") | Q(archetype__isnull=True)
    )
    clip = qs.order_by("-is_active", "-created_at").first()
    if clip:
        logger.debug(f"Found generic R2Video for {ex_slug}/{kind}")
        return clip

    # 3) другой архетип как крайний фоллбек
    # Ищем любое видео для этого упражнения и типа с другим архетипом
    code_pattern = f"{ex_slug}_{kind}"
    qs = R2Video.objects.filter(
        code__icontains=code_pattern,
        category='exercises'
    ).exclude(archetype=archetype)
    clip = qs.order_by("-is_active", "-created_at").first()
    if clip:
        logger.debug(f"Using fallback R2Video archetype {clip.archetype} for {ex_slug}/{kind}")
    return clip


def build_playlist(plan_json: Dict, archetype: str, strict_mode: bool = None) -> List[Dict]:
    """
    Build video playlist from workout plan JSON
    
    Args:
        plan_json: V2 schema workout plan
        archetype: User's trainer archetype (mentor/professional/peer)
        strict_mode: Enable strict validation (None = use settings default)
        
    Returns:
        List of playlist items with signed URLs and metadata
        
    Raises:
        ValueError: In strict mode when validation fails
    """
    # Initialize validator
    validator = StrictPlaylistValidator(strict_mode)
    out: List[Dict] = []
    weeks = plan_json.get("weeks", [])
    
    for w_idx, week in enumerate(weeks, start=1):
        for d_idx, day in enumerate(week.get("days", []), start=1):
            is_rest_day = day.get("is_rest_day", False)
            
            for block in day.get("blocks", []):
                btype = block.get("type")
                
                if btype in ("warmup", "main", "cooldown"):
                    # Process exercise blocks
                    for ex in block.get("exercises", []):
                        slug = ex.get("exercise_slug") or ex.get("slug")  # Support both new and legacy formats
                        
                        # Validate exercise exists (strict mode may raise ValueError)
                        validator.validate_exercise_exists(slug)
                        
                        if not slug:
                            continue
                            
                        # Validate video availability (strict mode may raise ValueError)
                        validator.validate_video_availability(slug, "instruction", archetype)
                            
                        # Get instruction video for the exercise
                        clip = _resolve_clip(slug, "instruction", archetype)
                        if clip:
                            # Safe handling of file fields that might be None or invalid
                            signed_url = ""
                            poster_cdn = ""
                            
                            try:
                                # Use structured path URL generation instead of r2_file
                                signed_url = MediaService.get_video_url(clip)
                            except (AttributeError, TypeError) as e:
                                logger.warning(f"Error generating video URL for R2Video {clip.code}: {e}")
                            
                            # R2Video не имеет прямой связи с exercise и poster_image
                            # Используем название видео как poster (опционально)
                            try:
                                poster_cdn = ""  # Пока без poster'ов для R2Video
                            except Exception as e:
                                logger.warning(f"Error handling poster for R2Video {clip.code}: {e}")
                            
                            out.append({
                                "week": w_idx,
                                "day": d_idx,
                                "block": btype,
                                "exercise_slug": slug,
                                "exercise_name": ex.get("name", slug),
                                "sets": ex.get("sets"),
                                "reps": ex.get("reps"),
                                "kind": "instruction",
                                "clip_id": clip.code,
                                "signed_url": signed_url,
                                "poster_cdn": poster_cdn,
                                "archetype": clip.archetype or archetype,
                                "duration_seconds": None,  # R2Video не хранит duration
                            })
                        
                        # Add technique/mistake videos if available (for UI hints)
                        for aux_kind in ("technique", "mistake"):
                            # Validate auxiliary videos (non-critical)
                            validator.validate_video_availability(slug, aux_kind, archetype)
                            
                            clip = _resolve_clip(slug, aux_kind, archetype)
                            if clip:
                                # Safe handling of file fields that might be None or invalid
                                signed_url = ""
                                poster_cdn = ""
                                
                                try:
                                    # Use structured path URL generation instead of r2_file
                                    signed_url = MediaService.get_video_url(clip)
                                except (AttributeError, TypeError) as e:
                                    logger.warning(f"Error generating video URL for {aux_kind} R2Video {clip.code}: {e}")
                                
                                try:
                                    poster_cdn = ""  # R2Video не имеет прямой связи с exercise.poster_image
                                except (AttributeError, TypeError) as e:
                                    logger.warning(f"Error handling poster for {aux_kind} R2Video {clip.code}: {e}")
                                
                                out.append({
                                    "week": w_idx,
                                    "day": d_idx,
                                    "block": f"{btype}_aux",
                                    "exercise_slug": slug,
                                    "exercise_name": ex.get("name", slug),
                                    "kind": aux_kind,
                                    "clip_id": clip.code,
                                    "signed_url": signed_url,
                                    "poster_cdn": poster_cdn,
                                    "archetype": clip.archetype or archetype,
                                    "duration_seconds": None,  # R2Video не хранит duration
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
                    
            # Validate playlist completeness for this day (strict mode may raise ValueError)
            day_items = [item for item in out if item.get("week") == w_idx and item.get("day") == d_idx]
            validator.validate_playlist_completeness(day_items, is_rest_day)
    
    # Log validation results
    report = validator.get_validation_report()
    if report['warnings']:
        logger.warning(f"Playlist validation warnings: {report['warnings']}")
    
    logger.info(f"Built playlist with {len(out)} items for archetype {archetype}")
    return out


def get_daily_playlist(plan_json: Dict, archetype: str, week: int, day: int, strict_mode: bool = None) -> List[Dict]:
    """
    Get playlist for a specific day
    
    Args:
        plan_json: V2 schema workout plan
        archetype: User's trainer archetype
        week: Week number (1-based)
        day: Day number (1-based)
        strict_mode: Enable strict validation (None = use settings default)
        
    Returns:
        Filtered playlist for the specific day
        
    Raises:
        ValueError: In strict mode when validation fails
    """
    full_playlist = build_playlist(plan_json, archetype, strict_mode)
    day_items = [
        item for item in full_playlist 
        if item.get("week") == week and item.get("day") == day
    ]
    logger.info(f"Filtered {len(day_items)} items for week {week}, day {day}")
    return day_items