"""
Storage audit utilities for verifying file existence in R2/S3
"""
import logging
import requests
from typing import List, Dict, Set
from django.conf import settings

from apps.core.services.media import MediaService

logger = logging.getLogger(__name__)


def check_video_file_exists(exercise_slug: str, video_type: str = 'technique', archetype: str = None) -> bool:
    """
    Check if a video file exists in storage for the given exercise
    
    Args:
        exercise_slug: Exercise slug (e.g., 'push-up', 'EX027_v2')
        video_type: Type of video ('technique', 'mistake', 'instruction')
        archetype: Archetype for archetype-specific videos
        
    Returns:
        True if file exists, False otherwise
    """
    try:
        # Generate expected file path based on video type
        if video_type == 'instruction' and archetype:
            file_path = f"videos/instructions/{exercise_slug}_instruction_{archetype}_model.mp4"
        elif video_type in ['technique', 'mistake']:
            file_path = f"videos/exercises/{exercise_slug}_{video_type}_model.mp4"
        else:
            return False
        
        # Get public URL
        public_url = MediaService.get_public_cdn_url(file_path)
        
        if not public_url:
            return False
        
        # Check if file exists by making HEAD request
        response = requests.head(public_url, timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        logger.debug(f"Error checking file existence for {exercise_slug}/{video_type}: {e}")
        return False


def audit_exercise_video_coverage(exercise_slugs: List[str]) -> Dict[str, Dict]:
    """
    Audit video coverage for a list of exercises
    
    Args:
        exercise_slugs: List of exercise slugs to check
        
    Returns:
        Dict with coverage information per exercise
    """
    results = {}
    archetypes = ['mentor', 'professional', 'peer']
    video_types = ['technique', 'mistake']
    
    for slug in exercise_slugs:
        coverage = {
            'technique': False,
            'mistake': False,
            'instructions': {}
        }
        
        # Check technique and mistake videos
        for video_type in video_types:
            coverage[video_type] = check_video_file_exists(slug, video_type)
        
        # Check instruction videos per archetype
        for archetype in archetypes:
            coverage['instructions'][archetype] = check_video_file_exists(
                slug, 'instruction', archetype
            )
        
        # Calculate coverage score
        coverage['score'] = (
            int(coverage['technique']) + 
            int(coverage['mistake']) + 
            sum(coverage['instructions'].values())
        ) / (2 + len(archetypes))
        
        coverage['complete'] = coverage['score'] >= 0.8  # 80% coverage threshold
        
        results[slug] = coverage
    
    return results


def find_orphaned_files() -> List[str]:
    """
    Find files in storage that don't correspond to any exercise in database
    
    Returns:
        List of potentially orphaned file paths
    """
    # This would require more complex S3/R2 API usage to list all files
    # For now, return empty list as placeholder
    logger.info("Orphaned file detection not yet implemented")
    return []


def generate_storage_audit_report(exercise_slugs: List[str]) -> Dict:
    """
    Generate comprehensive storage audit report
    
    Args:
        exercise_slugs: List of exercise slugs to audit
        
    Returns:
        Audit report dictionary
    """
    coverage_data = audit_exercise_video_coverage(exercise_slugs)
    
    # Calculate summary statistics
    total_exercises = len(exercise_slugs)
    complete_coverage = sum(1 for c in coverage_data.values() if c['complete'])
    avg_coverage = sum(c['score'] for c in coverage_data.values()) / total_exercises if total_exercises > 0 else 0
    
    # Find problematic exercises
    missing_technique = [slug for slug, c in coverage_data.items() if not c['technique']]
    missing_mistake = [slug for slug, c in coverage_data.items() if not c['mistake']]
    missing_instructions = []
    
    for slug, coverage in coverage_data.items():
        missing_archetypes = [
            arch for arch, exists in coverage['instructions'].items() 
            if not exists
        ]
        if missing_archetypes:
            missing_instructions.append({
                'slug': slug,
                'missing_archetypes': missing_archetypes
            })
    
    return {
        'summary': {
            'total_exercises': total_exercises,
            'complete_coverage': complete_coverage,
            'complete_coverage_pct': (complete_coverage / total_exercises * 100) if total_exercises > 0 else 0,
            'avg_coverage_score': avg_coverage * 100
        },
        'issues': {
            'missing_technique': missing_technique,
            'missing_mistake': missing_mistake,
            'missing_instructions': missing_instructions
        },
        'detailed_coverage': coverage_data
    }