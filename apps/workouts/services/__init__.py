from .playlist_v2 import build_playlist, get_daily_playlist


# Backward compatibility alias
class VideoPlaylistBuilder:
    """Legacy compatibility class - use build_playlist function instead"""
    @staticmethod
    def build_playlist(plan_json, archetype):
        return build_playlist(plan_json, archetype)

__all__ = ['build_playlist', 'get_daily_playlist', 'VideoPlaylistBuilder']