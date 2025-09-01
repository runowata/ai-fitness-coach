#!/usr/bin/env python
"""
Analyze R2 video structure for playlist generation
"""
import boto3
from collections import defaultdict
import re

# Cloudflare R2 credentials
ACCESS_KEY_ID = '3a9fd5a6b38ec994e057e33c1096874e'
SECRET_ACCESS_KEY = '0817f9a3154b63b1968620a966e05e36f80fca0308ba91d9c8bf65e8622baa13'
ENDPOINT_URL = 'https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com'
BUCKET_NAME = 'ai-fitness-media'

# Create S3 client for R2
s3_client = boto3.client(
    's3',
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=SECRET_ACCESS_KEY,
    region_name='auto'
)

def analyze_videos():
    """Analyze video structure in R2"""
    try:
        # Get all video files
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=BUCKET_NAME, Prefix='videos/')
        
        categories = defaultdict(list)
        archetypes = defaultdict(list)
        exercise_types = defaultdict(set)
        
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    if not key.endswith('.mp4'):
                        continue
                    
                    # Parse video path: videos/category/filename.mp4
                    parts = key.split('/')
                    if len(parts) >= 3:
                        category = parts[1]  # exercises, motivation, etc
                        filename = parts[2].replace('.mp4', '')
                        
                        categories[category].append(filename)
                        
                        # Check for archetype markers (bro, mentor, professional)
                        if 'bro' in filename.lower():
                            archetypes['peer'].append(filename)
                        elif 'mentor' in filename.lower():
                            archetypes['mentor'].append(filename)
                        elif 'professional' in filename.lower():
                            archetypes['professional'].append(filename)
                        
                        # Identify exercise types
                        if category == 'exercises':
                            # Parse exercise type from filename
                            if 'warmup' in filename or 'разминка' in filename:
                                exercise_types['warmup'].add(filename)
                            elif 'endurance' in filename or 'выносливость' in filename:
                                exercise_types['endurance'].add(filename)
                            elif 'cooldown' in filename or 'relax' in filename or 'расслабление' in filename:
                                exercise_types['cooldown'].add(filename)
                            elif 'technique' in filename:
                                # Main exercises show technique
                                exercise_types['main'].add(filename)
        
        # Print analysis
        print("=== VIDEO ANALYSIS FOR PLAYLIST GENERATION ===\n")
        
        print("📁 Videos by Category:")
        for cat, files in sorted(categories.items()):
            print(f"\n{cat}: {len(files)} videos")
            # Show sample files
            for file in files[:5]:
                print(f"  - {file}")
            if len(files) > 5:
                print(f"  ... and {len(files)-5} more")
        
        print("\n🏋️ Exercise Types Found:")
        for ex_type, files in exercise_types.items():
            print(f"\n{ex_type}: {len(files)} unique exercises")
            for file in list(files)[:3]:
                print(f"  - {file}")
        
        print("\n👨‍🏫 Videos by Archetype (Trainers):")
        for arch, files in archetypes.items():
            print(f"\n{arch}: {len(files)} videos")
            # Separate by type
            motivation_vids = [f for f in files if 'motivation' in categories and f in categories['motivation']]
            print(f"  Motivation/Speech videos: {len(motivation_vids)}")
            for vid in motivation_vids[:3]:
                print(f"    - {vid}")
        
        # Check if we have enough videos for 21 days
        print("\n📊 Feasibility Check for 21-day Program:")
        
        # Need 11 exercise videos per day for 21 days = 231 unique exercises
        total_exercises = len(categories.get('exercises', []))
        print(f"Total exercise videos: {total_exercises}")
        print(f"Needed for 21 days (11 per day): 231")
        print(f"Status: {'✅ ENOUGH' if total_exercises >= 231 else '❌ NOT ENOUGH'}")
        
        # For trainer videos, they can repeat
        trainer_videos = sum(len(v) for v in archetypes.values())
        print(f"\nTotal trainer/motivation videos: {trainer_videos}")
        print(f"These can repeat across 21 days ✅")
        
        return categories, exercise_types, archetypes
        
    except Exception as e:
        print(f"Error: {e}")
        return {}, {}, {}

if __name__ == "__main__":
    analyze_videos()