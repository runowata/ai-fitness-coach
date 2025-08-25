#!/usr/bin/env python3
"""
Create motivation videos CSV based on actual R2 structure
"""
import boto3
import csv
import re
from collections import defaultdict

def get_r2_client():
    """Initialize R2 S3 client with actual credentials"""
    access_key = '3a9fd5a6b38ec994e057e33c1096874e'
    secret_key = '0817f9a3154b63b1968620a966e05e36f80fca0308ba91d9c8bf65e8622baa13'
    endpoint_url = 'https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com'
    
    return boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name='auto'
    )

def scan_motivation_videos():
    """Scan all motivation videos in R2"""
    s3_client = get_r2_client()
    bucket_name = 'ai-fitness-media'
    
    motivation_videos = []
    weekly_videos = []
    
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        
        print("🎬 Scanning motivation videos in R2...")
        
        for page in paginator.paginate(Bucket=bucket_name, Prefix='videos/'):
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                key = obj['Key']
                
                # Skip directories
                if key.endswith('/'):
                    continue
                
                # Parse motivation videos
                if '/motivation/' in key or '/weekly/' in key or '/final/' in key or '/progress/' in key:
                    parsed = parse_motivation_video(key)
                    if parsed:
                        if parsed['video_type'] == 'weekly':
                            weekly_videos.append(parsed)
                        else:
                            motivation_videos.append(parsed)
                        
        print(f"✅ Found {len(motivation_videos)} motivation videos")
        print(f"✅ Found {len(weekly_videos)} weekly videos")
        
        return {
            'motivation': motivation_videos,
            'weekly': weekly_videos
        }
        
    except Exception as e:
        print(f"❌ Error scanning R2: {e}")
        return None

def parse_motivation_video(filepath):
    """Parse motivation video file path"""
    if not filepath.startswith('videos/'):
        return None
    
    # Remove videos/ prefix and extension
    path = filepath[7:]  # Remove 'videos/'
    if '.' in path:
        path = path.rsplit('.', 1)[0]  # Remove extension
    
    parts = path.split('/')
    if len(parts) < 2:
        return None
    
    category = parts[0]  # motivation, weekly, final, progress, etc.
    filename = parts[-1]
    
    result = {
        'category': category,
        'filename': filename,
        'video_type': None,
        'archetype': None,
        'week_number': None,
        'day_number': None,
        'sequence': None,
        'original_path': filepath
    }
    
    # Parse different motivation video patterns
    if category == 'motivation':
        # Various motivation patterns
        result['video_type'] = 'motivation'
        
        # Extract archetype
        for arch in ['bro', 'sergeant', 'intellectual']:
            if arch in filename:
                result['archetype'] = arch
                break
        
        # Try to extract sequence numbers
        numbers = re.findall(r'\d+', filename)
        if numbers:
            result['sequence'] = int(numbers[-1])  # Use last number found
            
    elif category == 'weekly':
        # weekly_{archetype}_week{number}.mp4
        match = re.match(r'weekly_(.+)_week(\d+)', filename)
        if match:
            result['video_type'] = 'weekly'
            result['archetype'] = match.group(1)
            result['week_number'] = int(match.group(2))
            
    elif category in ['final', 'progress']:
        result['video_type'] = category
        
        # Extract archetype
        for arch in ['bro', 'sergeant', 'intellectual']:
            if arch in filename:
                result['archetype'] = arch
                break
        
        # Extract numbers
        numbers = re.findall(r'\d+', filename)
        if numbers:
            result['sequence'] = int(numbers[-1])
    
    return result if result['video_type'] else None

def map_archetype_to_new(old_archetype):
    """Map old R2 archetypes to new system"""
    mapping = {
        'bro': 'peer',           # Best Mate -> 113
        'sergeant': 'professional',  # Pro Coach -> 112
        'intellectual': 'mentor'     # Wise Mentor -> 111
    }
    return mapping.get(old_archetype, old_archetype)

def create_motivation_csv():
    """Create CSV with all motivation videos indexed by day and archetype"""
    
    print("🔍 Scanning motivation videos in R2...")
    r2_data = scan_motivation_videos()
    
    if not r2_data:
        print("❌ Failed to scan R2!")
        return
    
    motivation_videos = r2_data['motivation']
    weekly_videos = r2_data['weekly']
    
    # Create CSV for motivation videos
    csv_file = 'data/clean/motivation_videos.csv'
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'video_id', 'video_type', 'archetype_old', 'archetype_new', 
            'day_number', 'week_number', 'sequence', 'r2_file', 'category', 
            'description_ru', 'description_en'
        ])
        
        # Process regular motivation videos
        for video in motivation_videos:
            archetype_old = video['archetype'] or 'unknown'
            archetype_new = map_archetype_to_new(archetype_old)
            
            # Generate video ID
            video_id = f"MOT_{archetype_old.upper()}_{video['sequence'] or 1:03d}"
            
            # Distribute videos across 21 training days
            # Each archetype needs videos for 21 days
            day_number = ((video['sequence'] or 1) - 1) % 21 + 1
            week_number = ((video['sequence'] or 1) - 1) // 7 + 1
            
            # Generate descriptions
            descriptions = {
                'motivation': ("Мотивационное видео для поддержания энтузиазма", 
                              "Motivational video to maintain enthusiasm"),
                'final': ("Финальное мотивационное видео", 
                         "Final motivational video"),
                'progress': ("Видео о прогрессе тренировок", 
                           "Training progress video")
            }
            
            desc_ru, desc_en = descriptions.get(video['category'], 
                                               ("Мотивационный контент", "Motivational content"))
            
            writer.writerow([
                video_id,
                video['category'],
                archetype_old,
                archetype_new,
                day_number,
                week_number,
                video['sequence'] or 1,
                video['original_path'],
                video['category'],
                desc_ru,
                desc_en
            ])
        
        # Process weekly videos
        for video in weekly_videos:
            archetype_old = video['archetype'] or 'unknown'
            archetype_new = map_archetype_to_new(archetype_old)
            
            video_id = f"WEEK_{archetype_old.upper()}_W{video['week_number']:02d}"
            
            writer.writerow([
                video_id,
                'weekly',
                archetype_old,
                archetype_new,
                0,  # Weekly videos aren't tied to specific days
                video['week_number'],
                video['week_number'],
                video['original_path'],
                'weekly',
                f"Еженедельное мотивационное видео - неделя {video['week_number']}",
                f"Weekly motivational video - week {video['week_number']}"
            ])
    
    print(f"✅ Created motivation CSV: {csv_file}")
    
    # Show breakdown
    print(f"\n📊 MOTIVATION VIDEO BREAKDOWN:")
    print(f"  Regular motivation: {len(motivation_videos)} videos")
    print(f"  Weekly videos: {len(weekly_videos)} videos")
    print(f"  Total: {len(motivation_videos) + len(weekly_videos)} videos")
    
    # Show archetype distribution
    archetype_count = defaultdict(int)
    for video in motivation_videos + weekly_videos:
        archetype_count[video['archetype']] += 1
    
    print(f"\n📊 ARCHETYPE DISTRIBUTION:")
    for archetype, count in sorted(archetype_count.items()):
        new_archetype = map_archetype_to_new(archetype)
        print(f"  {archetype} -> {new_archetype}: {count} videos")

def create_playlist_structure_csv():
    """Create CSV showing ideal playlist structure for 21 days"""
    
    csv_file = 'data/clean/playlist_structure_21_days.csv'
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'day_number', 'week_number', 'warmup_videos', 'main_videos', 
            'endurance_videos', 'relaxation_videos', 'motivation_videos', 
            'total_videos_per_day', 'notes'
        ])
        
        # 21 training days structure
        for day in range(1, 22):
            week = (day - 1) // 7 + 1
            
            # Standard structure per day according to ideal playlist
            warmup_videos = 2      # 2 warmup exercises
            main_videos = 8        # 8 main exercises  
            endurance_videos = 3   # 3 endurance exercises
            relaxation_videos = 3  # 3 relaxation exercises
            motivation_videos = 0  # Will be added via separate system
            
            total_per_day = warmup_videos + main_videos + endurance_videos + relaxation_videos
            
            notes = f"Стандартная структура дня {day}, неделя {week}"
            
            writer.writerow([
                day, week, warmup_videos, main_videos, 
                endurance_videos, relaxation_videos, motivation_videos,
                total_per_day, notes
            ])
    
    print(f"✅ Created playlist structure CSV: {csv_file}")
    print(f"📊 PLAYLIST STRUCTURE:")
    print(f"  21 training days")
    print(f"  16 exercise videos per day")
    print(f"  Total: 336 exercise videos (21 × 16)")
    print(f"  + 315+ motivation videos")
    print(f"  = 651+ total videos in system")

if __name__ == "__main__":
    create_motivation_csv()
    print("\n" + "="*50)
    create_playlist_structure_csv()