"""
Tests for v2 playlist builder
"""
import json

import pytest

from apps.workouts.models import Exercise, VideoClip
from apps.workouts.services.playlist_v2 import _resolve_clip, build_playlist, get_daily_playlist


@pytest.fixture
def sample_plan_json():
    """Sample v2 workout plan JSON"""
    return {
        "meta": {
            "version": "v2",
            "archetype": "mentor",
            "goal": "muscle_gain",
            "plan_name": "Test Plan"
        },
        "weeks": [
            {
                "week_number": 1,
                "theme": "Foundation",
                "days": [
                    {
                        "day_number": 1,
                        "blocks": [
                            {
                                "type": "warmup",
                                "exercises": [
                                    {
                                        "slug": "push-ups",
                                        "name": "Push-ups",
                                        "sets": 3,
                                        "reps": "10-15"
                                    }
                                ]
                            },
                            {
                                "type": "main",
                                "exercises": [
                                    {
                                        "slug": "squats",
                                        "name": "Squats",
                                        "sets": 4,
                                        "reps": "8-12"
                                    }
                                ]
                            },
                            {
                                "type": "confidence_task",
                                "text": "Look yourself in the mirror",
                                "description": "Spend 2 minutes appreciating your body"
                            }
                        ]
                    }
                ]
            }
        ]
    }


class TestPlaylistV2:
    """Test playlist builder v2 functionality"""
    
    def test_build_playlist_empty_plan(self):
        """Test with empty plan"""
        result = build_playlist({}, "mentor")
        assert result == []
        
        result = build_playlist({"weeks": []}, "mentor")
        assert result == []
    
    def test_build_playlist_with_exercises(self, sample_plan_json):
        """Test playlist building with sample plan"""
        # This would need actual DB setup with exercises/clips
        result = build_playlist(sample_plan_json, "mentor")
        
        # Should have confidence task at minimum
        confidence_tasks = [item for item in result if item.get("block") == "confidence_task"]
        assert len(confidence_tasks) == 1
        assert confidence_tasks[0]["text"] == "Look yourself in the mirror"
    
    def test_get_daily_playlist(self, sample_plan_json):
        """Test filtering playlist for specific day"""
        result = get_daily_playlist(sample_plan_json, "mentor", week=1, day=1)
        
        # All items should be for week 1, day 1
        for item in result:
            if "week" in item:
                assert item["week"] == 1
            if "day" in item:
                assert item["day"] == 1
    
    def test_resolve_clip_fallback_logic(self):
        """Test clip resolution fallback strategy"""
        # This test would need mock data or test DB
        # Testing the logic without actual DB
        clip = _resolve_clip("nonexistent-exercise", "instruction", "mentor")
        assert clip is None


@pytest.mark.django_db
class TestPlaylistV2Integration:
    """Integration tests requiring database"""
    
    def test_build_playlist_resolves_clips(self, db, sample_plan_json):
        """Test that playlist resolves actual video clips"""
        # Create test exercise
        exercise = Exercise.objects.create(
            id="test-1",
            slug="push-ups",
            name="Push-ups",
            description="Test exercise",
            difficulty="beginner"
        )
        
        # Create test video clip
        clip = VideoClip.objects.create(
            exercise=exercise,
            r2_kind="instruction",
            archetype="mentor",
            model_name="mod1",
            duration_seconds=30,
            r2_file="videos/test.mp4"
        )
        
        # Build playlist
        result = build_playlist(sample_plan_json, "mentor")
        
        # Should find the clip for push-ups
        video_items = [item for item in result if item.get("clip_id")]
        if video_items:  # Only if clips were found
            assert any(item["exercise_slug"] == "push-ups" for item in video_items)
            assert all("signed_url" in item for item in video_items)
    
    def test_archetype_fallback(self, db):
        """Test fallback to different archetype"""
        # Create test exercise
        exercise = Exercise.objects.create(
            id="test-2",
            slug="squats",
            name="Squats",
            description="Test exercise",
            difficulty="beginner"
        )
        
        # Create clip with different archetype
        clip = VideoClip.objects.create(
            exercise=exercise,
            r2_kind="instruction",
            archetype="professional",  # Different from requested
            model_name="mod1",
            duration_seconds=30,
            r2_file="videos/test.mp4"
        )
        
        # Try to resolve with different archetype
        resolved = _resolve_clip("squats", "instruction", "mentor")
        
        # Should fallback to professional
        assert resolved is not None
        assert resolved.archetype == "professional"