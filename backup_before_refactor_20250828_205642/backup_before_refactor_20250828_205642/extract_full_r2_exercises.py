#!/usr/bin/env python3
"""
Extract all 271 exercises from R2 storage and create complete CSV
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

def scan_full_r2_structure():
    """Scan entire R2 structure and extract all video data"""
    s3_client = get_r2_client()
    bucket_name = 'ai-fitness-media'
    
    all_files = []
    exercises = set()
    video_types = defaultdict(int)
    archetypes = set()
    
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        
        print("🔍 Scanning all videos in R2...")
        
        for page in paginator.paginate(Bucket=bucket_name, Prefix='videos/'):
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                key = obj['Key']
                size = obj['Size']
                
                # Skip directories
                if key.endswith('/'):
                    continue
                
                all_files.append({
                    'key': key,
                    'size': size,
                    'size_mb': round(size / (1024*1024), 2)
                })
                
                # Parse different video patterns
                parsed = parse_video_file(key)
                if parsed:
                    exercises.add(parsed['exercise_id'])
                    video_types[parsed['video_type']] += 1
                    if parsed['archetype']:
                        archetypes.add(parsed['archetype'])
                    
        print(f"✅ Found {len(all_files)} total files")
        print(f"✅ Found {len(exercises)} unique exercises")
        print(f"✅ Found {len(archetypes)} archetypes: {sorted(archetypes)}")
        
        return {
            'all_files': all_files,
            'exercises': sorted(exercises), 
            'video_types': dict(video_types),
            'archetypes': sorted(archetypes)
        }
        
    except Exception as e:
        print(f"❌ Error scanning R2: {e}")
        return None

def parse_video_file(filepath):
    """Parse video file to extract metadata"""
    if not filepath.startswith('videos/'):
        return None
    
    # Remove videos/ prefix and extension
    path = filepath[7:]  # Remove 'videos/'
    if '.' in path:
        path = path.rsplit('.', 1)[0]  # Remove extension
    
    parts = path.split('/')
    if len(parts) < 2:
        return None
    
    category = parts[0]  # exercises, instructions, reminders, motivation, etc.
    filename = parts[-1]
    
    result = {
        'category': category,
        'exercise_id': None,
        'video_type': None,
        'archetype': None,
        'model': None,
        'original_path': filepath
    }
    
    # Parse different patterns
    if category == 'exercises' and '/explain/' not in filepath:
        # videos/exercises/{exercise}_technique_{model}.mp4
        match = re.match(r'(.+)_(technique|mistake)_(.+)', filename)
        if match:
            result['exercise_id'] = match.group(1)
            result['video_type'] = match.group(2)
            result['model'] = match.group(3)
            return result
            
    elif category == 'exercises' and '/explain/' in filepath:
        # videos/exercises/explain/{exercise}_explain_{model}.mp4
        match = re.match(r'(.+)_explain_(.+)', filename)
        if match:
            result['exercise_id'] = match.group(1)
            result['video_type'] = 'explain'
            result['model'] = match.group(2)
            return result
            
    elif category == 'instructions':
        # videos/instructions/{exercise}_instruction_{archetype}_{model}.mp4
        match = re.match(r'(.+)_instruction_(.+)_(.+)', filename)
        if match:
            result['exercise_id'] = match.group(1)
            result['video_type'] = 'instruction'
            result['archetype'] = match.group(2)
            result['model'] = match.group(3)
            return result
            
    elif category == 'reminders':
        # videos/reminders/{exercise}_reminder_{archetype}_{number}.mp4
        match = re.match(r'(.+)_reminder_(.+)_(\d+)', filename)
        if match:
            result['exercise_id'] = match.group(1)
            result['video_type'] = 'reminder'
            result['archetype'] = match.group(2)
            result['model'] = f'r{match.group(3)}'
            return result
            
    elif category in ['motivation', 'intros', 'closing', 'weekly', 'final', 'progress']:
        # Various motivation video patterns
        result['video_type'] = category
        result['exercise_id'] = f'{category}_video'
        
        # Try to extract archetype from filename
        for arch in ['best_mate', 'pro_coach', 'wise_mentor', 'bro', 'sergeant', 'intellectual']:
            if arch in filename:
                result['archetype'] = arch
                break
                
        return result
    
    return result if result['exercise_id'] else None

def categorize_exercise(exercise_id):
    """Determine category and properties from exercise ID"""
    if exercise_id.startswith('warmup_'):
        return {
            'category': 'warmup',
            'exercise_type': 'mobility',
            'level': 'beginner',
            'muscle_group': 'Все тело'
        }
    elif exercise_id.startswith('main_'):
        return {
            'category': 'main',
            'exercise_type': 'strength', 
            'level': 'intermediate',
            'muscle_group': 'Мышцы кора'
        }
    elif exercise_id.startswith('endurance_'):
        return {
            'category': 'endurance',
            'exercise_type': 'cardio',
            'level': 'intermediate', 
            'muscle_group': 'Все тело'
        }
    elif exercise_id.startswith('relaxation_'):
        return {
            'category': 'relaxation',
            'exercise_type': 'flexibility',
            'level': 'beginner',
            'muscle_group': 'Все тело'
        }
    else:
        return {
            'category': 'unknown',
            'exercise_type': 'strength',
            'level': 'intermediate',
            'muscle_group': 'Не определено'
        }

def generate_exercise_names():
    """Generate Russian and English names for exercises"""
    
    # Base names for different categories
    warmup_names = [
        ("Вращения тазом", "Hip Circles"),
        ("Махи ногами", "Leg Swings"), 
        ("Круговые движения плечами", "Shoulder Rolls"),
        ("Наклоны туловища", "Torso Bends"),
        ("Кошка-Корова", "Cat-Cow Pose"),
        ("Ходьба на месте", "High Knees Marching"),
        ("Прыжки на месте", "Jumping Jacks Light"),
        ("Вращения суставов", "Joint Rotations"),
        ("Наклоны таза", "Pelvic Tilts"),
        ("Повороты корпуса", "Torso Twists"),
        ("Мостик активация", "Glute Bridge Activation"),
        ("Приседания разминочные", "Warm-up Squats"),
        ("Отжимания от стены", "Wall Push-ups"),
        ("Червяк", "Inchworm"),
        ("Выпады разминочные", "Warm-up Lunges"),
    ]
    
    main_names = [
        ("Приседания", "Squats"),
        ("Отжимания", "Push-ups"),
        ("Выпады", "Lunges"),
        ("Планка", "Plank"),
        ("Мостик", "Glute Bridge"),
        ("Подъемы ног", "Leg Raises"),
        ("Скручивания", "Crunches"),
        ("Супермен", "Superman"),
        ("Подтягивания", "Pull-ups"),
        ("Берпи", "Burpees"),
        ("Жим", "Press"),
        ("Тяга", "Rows"),
        ("Присед-прыжок", "Jump Squats"),
        ("Выпад-прыжок", "Jumping Lunges"),
        ("Подъем на носки", "Calf Raises"),
    ]
    
    endurance_names = [
        ("Кардио-интервал", "Cardio Interval"),
        ("Высокоинтенсивный бег", "High Intensity Running"),
        ("Прыжки", "Jumping Exercise"),
        ("Кардио-микс", "Cardio Mix"),
        ("Интенсив", "High Intensity"),
        ("Выносливость", "Endurance Training"),
        ("Кардио-блок", "Cardio Block"),
        ("Аэробная нагрузка", "Aerobic Exercise"),
        ("Функциональная тренировка", "Functional Training"),
        ("Круговая тренировка", "Circuit Training"),
    ]
    
    relaxation_names = [
        ("Растяжка спины", "Back Stretch"),
        ("Растяжка ног", "Leg Stretch"), 
        ("Растяжка плеч", "Shoulder Stretch"),
        ("Растяжка груди", "Chest Stretch"),
        ("Растяжка бедер", "Hip Stretch"),
        ("Поза ребенка", "Child's Pose"),
        ("Скручивание", "Spinal Twist"),
        ("Расслабление", "Relaxation Pose"),
        ("Медитативная растяжка", "Meditative Stretch"),
        ("Восстановление", "Recovery Stretch"),
    ]
    
    return {
        'warmup': warmup_names,
        'main': main_names, 
        'endurance': endurance_names,
        'relaxation': relaxation_names
    }

def create_full_exercise_csv():
    """Create complete CSV with all exercises from R2"""
    
    print("🔍 Scanning R2 storage structure...")
    r2_data = scan_full_r2_structure()
    
    if not r2_data:
        print("❌ Failed to scan R2!")
        return
    
    exercises = [ex for ex in r2_data['exercises'] if not ex.endswith('_video')]
    
    print(f"\n📊 R2 STRUCTURE ANALYSIS:")
    print(f"  Total files: {len(r2_data['all_files'])}")
    print(f"  Total exercises: {len(exercises)}")
    print(f"  Video types: {r2_data['video_types']}")
    print(f"  Archetypes: {r2_data['archetypes']}")
    
    if not exercises:
        print("❌ No exercises found in R2!")
        return
    
    # Generate names
    names = generate_exercise_names()
    
    # Create CSV
    csv_file = 'data/clean/exercises_complete_r2.csv'
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'id', 'name_ru', 'name_en', 'description', 'muscle_group', 
            'exercise_type', 'level', 'ai_tags', 'category'
        ])
        
        for exercise_id in exercises:
            props = categorize_exercise(exercise_id)
            category = props['category']
            
            # Extract number from ID 
            number_match = re.search(r'(\d+)', exercise_id)
            number = int(number_match.group(1)) if number_match else 1
            
            # Get appropriate name list
            name_list = names.get(category, names['main'])
            
            # Cycle through names
            name_index = (number - 1) % len(name_list)
            base_ru, base_en = name_list[name_index]
            
            # Add variation number if needed
            variation = ((number - 1) // len(name_list)) + 1
            if variation > 1:
                name_ru = f"{base_ru} {variation}"
                name_en = f"{base_en} {variation}"
            else:
                name_ru = base_ru
                name_en = base_en
                
            # Generate description
            descriptions = {
                'warmup': f"Разминочное упражнение для подготовки тела к основной нагрузке. {name_ru} помогает активировать мышцы и улучшить подвижность суставов.",
                'main': f"Основное силовое упражнение для развития мышечной силы и выносливости. {name_ru} является ключевым элементом тренировочной программы.",
                'endurance': f"Кардио упражнение для развития выносливости и улучшения сердечно-сосудистой системы. {name_ru} повышает общую физическую подготовку.",
                'relaxation': f"Упражнение на растяжку и расслабление для восстановления после тренировки. {name_ru} помогает снять напряжение и улучшить гибкость."
            }
            
            # Generate AI tags
            ai_tags_map = {
                'warmup': '["Разминка", "Подвижность", "Подготовка", "Активация"]',
                'main': '["Сила", "Выносливость", "Основная тренировка", "Мышечная масса"]',
                'endurance': '["Кардио", "Выносливость", "Сжигание калорий", "Интенсивность"]', 
                'relaxation': '["Растяжка", "Расслабление", "Восстановление", "Гибкость"]'
            }
            
            writer.writerow([
                exercise_id,
                name_ru,
                name_en,
                descriptions.get(category, "Упражнение для физической подготовки"),
                props['muscle_group'],
                props['exercise_type'], 
                props['level'],
                ai_tags_map.get(category, '["Тренировка"]'),
                category
            ])
    
    print(f"✅ Created complete CSV with {len(exercises)} exercises: {csv_file}")
    
    # Show breakdown
    breakdown = defaultdict(int)
    for exercise_id in exercises:
        category = categorize_exercise(exercise_id)['category']
        breakdown[category] += 1
    
    print("\n📊 BREAKDOWN:")
    for category, count in sorted(breakdown.items()):
        print(f"  {category}: {count} exercises")

if __name__ == "__main__":
    create_full_exercise_csv()