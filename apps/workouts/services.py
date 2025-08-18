import json
import os
from typing import List, Dict
from .models import Exercise, DailyWorkout


class VideoPlaylistBuilder:
    """Service to build video playlist from SYSTEM_616_VIDEOS.json"""
    
    def __init__(self):
        # Load video data once
        json_path = os.path.join(os.path.dirname(__file__), '../../media_lists/SYSTEM_616_VIDEOS.json')
        with open(json_path, 'r') as f:
            self.video_data = json.load(f)
    
    def build_workout_playlist(self, workout: DailyWorkout, user_archetype: str) -> List[Dict]:
        """
        Build video playlist based on workout.playlist JSON
        """
        playlist = []
        
        for item in workout.playlist:
            if item['type'] == 'exercise':
                # Find exercise video by slug
                video_url = self._get_exercise_video(item['exercise_slug'], item['category'])
                if video_url:
                    playlist.append({
                        'type': 'exercise',
                        'slug': item['exercise_slug'],
                        'url': video_url
                    })
            elif item['type'] == 'motivational':
                # Find motivational video by category and day
                video_url = self._get_motivational_video(
                    item['category'], 
                    workout.day_number,
                    user_archetype
                )
                if video_url:
                    playlist.append({
                        'type': 'motivational',
                        'category': item['category'],
                        'url': video_url
                    })
        
        return playlist
    
    def _get_exercise_video(self, exercise_slug: str, category: str) -> str:
        """Get exercise video URL from SYSTEM_616_VIDEOS.json"""
        for exercise_data in self.video_data.get('exercises_by_category', {}).get(category, []):
            if exercise_data['exercise_slug'] == exercise_slug:
                return exercise_data['cloudflare_url']
        return None
    
    def _get_motivational_video(self, category: str, day_number: int, archetype: str) -> str:
        """Get motivational video URL based on category, day and archetype"""
        # This would match motivational videos based on type and archetype
        # Simplified for now
        motivational_videos = self.video_data.get('motivational_by_type', {}).get(category, [])
        
        # Filter by archetype if available
        archetype_videos = [v for v in motivational_videos if v.get('archetype') == archetype]
        
        if archetype_videos:
            # Return video for this day (cycling through available)
            index = (day_number - 1) % len(archetype_videos)
            return archetype_videos[index]['cloudflare_url']
        
        return None