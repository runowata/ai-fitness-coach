#!/usr/bin/env python
"""
Debug script to check video system status on production
Run with: python debug_video_system.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from apps.workouts.models import VideoClip, Exercise, DailyWorkout, WorkoutPlan
from apps.workouts.services import VideoPlaylistBuilder
from apps.users.models import User
import json


def check_video_files():
    """Check if video files exist on disk"""
    print("\n=== CHECKING VIDEO FILES ===")
    
    video_dir = os.path.join(settings.STATIC_ROOT, 'videos')
    print(f"Video directory: {video_dir}")
    print(f"Directory exists: {os.path.exists(video_dir)}")
    
    if os.path.exists(video_dir):
        video_count = 0
        for root, dirs, files in os.walk(video_dir):
            for file in files:
                if file.endswith('.mp4'):
                    video_count += 1
                    if video_count <= 5:  # Show first 5 videos
                        print(f"  Found: {os.path.join(root, file)}")
        
        print(f"\nTotal video files found: {video_count}")
    else:
        print("ERROR: Video directory does not exist!")


def check_video_clips():
    """Check VideoClip database records"""
    print("\n=== CHECKING VIDEO CLIPS IN DATABASE ===")
    
    total_clips = VideoClip.objects.count()
    active_clips = VideoClip.objects.filter(is_active=True).count()
    placeholder_clips = VideoClip.objects.filter(is_placeholder=True).count()
    
    print(f"Total VideoClips: {total_clips}")
    print(f"Active VideoClips: {active_clips}")
    print(f"Placeholder VideoClips: {placeholder_clips}")
    
    # Check by type
    print("\nVideoClips by type:")
    for video_type in ['intro', 'technique', 'mistake', 'support', 'outro']:
        count = VideoClip.objects.filter(type=video_type).count()
        active_count = VideoClip.objects.filter(type=video_type, is_active=True).count()
        print(f"  {video_type}: {count} total, {active_count} active")
    
    # Check by archetype
    print("\nVideoClips by archetype:")
    for archetype in ['daddy', 'warrior', 'explorer', 'sage']:
        count = VideoClip.objects.filter(archetype=archetype).count()
        print(f"  {archetype}: {count}")
    
    # Sample some video clips
    print("\nSample VideoClips:")
    for clip in VideoClip.objects.filter(is_active=True)[:5]:
        print(f"  - {clip.type} | {clip.archetype} | {clip.exercise.name if clip.exercise else 'No exercise'}")
        print(f"    URL: {clip.url}")
        print(f"    File exists: {os.path.exists(os.path.join(settings.STATIC_ROOT, clip.url.lstrip('/')))}")


def check_exercises():
    """Check exercise records"""
    print("\n=== CHECKING EXERCISES ===")
    
    total_exercises = Exercise.objects.count()
    active_exercises = CSVExercise.objects.filter(is_active=True).count()
    
    print(f"Total exercises: {total_exercises}")
    print(f"Active exercises: {active_exercises}")
    
    # Check exercises with video clips
    exercises_with_videos = 0
    for exercise in CSVExercise.objects.filter(is_active=True):
        if exercise.video_clips.filter(is_active=True).exists():
            exercises_with_videos += 1
    
    print(f"Exercises with active video clips: {exercises_with_videos}")


def test_playlist_builder():
    """Test the VideoPlaylistBuilder with a real workout"""
    print("\n=== TESTING VIDEO PLAYLIST BUILDER ===")
    
    # Get a recent workout
    recent_workout = DailyWorkout.objects.filter(
        plan__is_active=True,
        is_rest_day=False
    ).order_by('-created_at').first()
    
    if not recent_workout:
        print("ERROR: No active workouts found!")
        return
    
    print(f"Testing with workout ID: {recent_workout.id}")
    print(f"Workout name: {recent_workout.name}")
    print(f"User: {recent_workout.plan.user.email}")
    print(f"Exercises: {len(recent_workout.exercises)}")
    
    # Get user archetype
    archetype = recent_workout.plan.user.profile.archetype
    print(f"User archetype: {archetype}")
    
    if not archetype:
        print("ERROR: User has no archetype set!")
        return
    
    # Build playlist
    builder = VideoPlaylistBuilder()
    playlist = builder.build_workout_playlist(recent_workout, archetype)
    
    print(f"\nPlaylist built with {len(playlist)} videos:")
    for i, video in enumerate(playlist):
        print(f"\n{i+1}. {video['title']}")
        print(f"   Type: {video['type']}")
        print(f"   URL: {video['url']}")
        print(f"   Duration: {video['duration']}s")
        
        # Check if file exists
        file_path = os.path.join(settings.STATIC_ROOT, video['url'].lstrip('/'))
        print(f"   File exists: {os.path.exists(file_path)}")


def check_specific_workout(workout_id):
    """Check a specific workout's video status"""
    print(f"\n=== CHECKING WORKOUT {workout_id} ===")
    
    try:
        workout = DailyWorkout.objects.get(id=workout_id)
        print(f"Workout found: {workout.name}")
        print(f"User: {workout.plan.user.email}")
        print(f"Is rest day: {workout.is_rest_day}")
        print(f"Exercises: {json.dumps(workout.exercises, indent=2)}")
        
        # Get archetype
        archetype = workout.plan.user.profile.archetype
        print(f"\nUser archetype: {archetype}")
        
        if not archetype:
            print("ERROR: User has no archetype!")
            return
        
        # Build playlist
        builder = VideoPlaylistBuilder()
        playlist = builder.build_workout_playlist(workout, archetype)
        
        print(f"\nPlaylist has {len(playlist)} videos")
        
        if not playlist:
            print("ERROR: No videos in playlist!")
            
            # Debug each exercise
            for exercise_data in workout.exercises:
                exercise_slug = exercise_data.get('exercise_slug')
                print(f"\nChecking exercise: {exercise_slug}")
                
                try:
                    exercise = Exercise.objects.get(slug=exercise_slug)
                    videos = exercise.video_clips.filter(is_active=True)
                    print(f"  Found {videos.count()} active videos for this exercise")
                    for v in videos[:3]:
                        print(f"    - {v.type} | {v.model_name}")
                except Exercise.DoesNotExist:
                    print(f"  ERROR: Exercise '{exercise_slug}' not found!")
        
    except DailyWorkout.DoesNotExist:
        print(f"ERROR: Workout {workout_id} not found!")


def check_static_url_config():
    """Check static file URL configuration"""
    print("\n=== CHECKING STATIC URL CONFIGURATION ===")
    
    print(f"STATIC_URL: {settings.STATIC_URL}")
    print(f"STATIC_ROOT: {settings.STATIC_ROOT}")
    print(f"DEBUG: {settings.DEBUG}")
    
    # Check if we're on Render
    is_render = os.environ.get('RENDER')
    print(f"Running on Render: {'Yes' if is_render else 'No'}")
    
    # Test a video URL
    if VideoClip.objects.filter(is_active=True).exists():
        clip = VideoClip.objects.filter(is_active=True).first()
        print(f"\nTest video URL: {clip.url}")
        print(f"Full static path: {os.path.join(settings.STATIC_ROOT, clip.url.lstrip('/'))}")


def main():
    """Run all checks"""
    print("=== VIDEO SYSTEM DEBUG REPORT ===")
    print(f"Environment: {'Production' if os.environ.get('RENDER') else 'Development'}")
    
    check_static_url_config()
    check_video_files()
    check_video_clips()
    check_exercises()
    test_playlist_builder()
    
    # Check specific workout if provided
    if len(sys.argv) > 1:
        workout_id = int(sys.argv[1])
        check_specific_workout(workout_id)
    else:
        print("\nTip: Run with workout ID to debug specific workout: python debug_video_system.py 567")


if __name__ == '__main__':
    main()