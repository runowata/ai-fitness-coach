#!/usr/bin/env python3
"""
Категоризация всех 271 упражнения по категориям для правильного формирования плейлистов
"""

import os
import csv
import re

def categorize_exercises_by_names():
    """Категоризирует упражнения на основе названий и содержания"""
    csv_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/EXERCISES_271_VIDEOS.csv'
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV файл не найден: {csv_file}")
        return {}
    
    exercises = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            exercises.append({
                'slug': row['exercise_slug'].strip(),
                'new_name': row.get('new_name', '').strip(),
                'category': row.get('category', '').strip()
            })
    
    print(f"📊 Загружено {len(exercises)} упражнений из CSV")
    
    # Определяем категории на основе ключевых слов
    categories = {
        'warmup': [],       # Разминка
        'main': [],         # Основные силовые
        'endurance': [],    # Сексуальная выносливость  
        'cooldown': []      # Расслабление/растяжка
    }
    
    # Ключевые слова для категоризации
    warmup_keywords = [
        'warmup', 'warm_up', 'circles', 'swings', 'bird_dog_warmup', 
        'bear_crawl_warmup', 'calf_raises_warmup', 'cat_cow_warmup',
        'butt_kicks', 'high_knees', 'leg_swings', 'arm_circles',
        'ankle_circles', 'shoulder_rolls', 'hip_circles'
    ]
    
    endurance_keywords = [
        'sexual', 'pelvic', 'kegel', 'hip_thrust', 'bridge_sexual',
        'curtsy_lunges_sexual', 'deep_squats_sexual', 'cat_cow_sexual',
        'dynamic_bridge_sexual', 'glute_bridge_sexual', 'hip_circles_sexual'
    ]
    
    cooldown_keywords = [
        'stretch', 'relax', 'pose', 'breathing', 'gratitude', 'final_',
        'corpse_pose', 'childs_pose', 'cobra_pose', 'butterfly_pose',
        'cat_pose_relax', 'calf_stretch_relax', 'butterfly_pose_relax',
        'chest_stretch_final', 'final_gratitude', 'final_hip_stretch',
        'final_relaxation', 'face_muscle_relax', 'deep_breathing'
    ]
    
    for exercise in exercises:
        slug = exercise['slug'].lower()
        new_name = exercise['new_name'].lower()
        
        # Проверяем категории по приоритету
        if any(keyword in slug for keyword in warmup_keywords):
            categories['warmup'].append(exercise)
        elif any(keyword in slug for keyword in endurance_keywords):
            categories['endurance'].append(exercise)
        elif any(keyword in slug for keyword in cooldown_keywords):
            categories['cooldown'].append(exercise)
        else:
            # Все остальные - основные упражнения
            categories['main'].append(exercise)
    
    return categories

def validate_categories(categories):
    """Проверяет правильность категоризации"""
    print(f"\n🔍 ВАЛИДАЦИЯ КАТЕГОРИЙ:")
    print("=" * 50)
    
    total = 0
    for category, exercises in categories.items():
        count = len(exercises)
        total += count
        print(f"{category:10}: {count:3d} упражнений")
        
        # Показываем примеры
        if exercises:
            examples = [ex['slug'] for ex in exercises[:3]]
            print(f"           Примеры: {', '.join(examples)}")
    
    print(f"\n📈 Общий итог: {total} упражнений")
    
    # Проверяем соотношения
    expected_ratios = {
        'warmup': (30, 50),     # 30-50 разминочных
        'main': (120, 160),     # 120-160 основных
        'endurance': (30, 50),  # 30-50 на выносливость
        'cooldown': (30, 50)    # 30-50 расслабляющих
    }
    
    print(f"\n⚖️ ПРОВЕРКА СООТНОШЕНИЙ:")
    for category, (min_val, max_val) in expected_ratios.items():
        count = len(categories[category])
        status = "✅" if min_val <= count <= max_val else "⚠️"
        print(f"{category:10}: {count:3d} (ожидается {min_val}-{max_val}) {status}")

def save_categorized_lists(categories):
    """Сохраняет списки упражнений по категориям"""
    print(f"\n💾 СОХРАНЕНИЕ СПИСКОВ ПО КАТЕГОРИЯМ:")
    
    for category, exercises in categories.items():
        file_path = f'/Users/alexbel/Desktop/AI Fitness Coach/prompts/exercises_{category}.txt'
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# УПРАЖНЕНИЯ КАТЕГОРИИ: {category.upper()}\n")
            f.write(f"# Количество: {len(exercises)} упражнений\n")
            f.write(f"# Сгенерировано автоматически\n\n")
            
            # Записываем exercise_slug через запятую
            slugs = [ex['slug'] for ex in exercises]
            
            # Форматируем по 8 упражнений в строке для читаемости
            for i in range(0, len(slugs), 8):
                line_slugs = slugs[i:i+8]
                f.write(', '.join(line_slugs))
                if i + 8 < len(slugs):
                    f.write(',')
                f.write('\n')
        
        print(f"  ✅ {category}: сохранено в {file_path}")

def create_playlist_schema():
    """Создает схему плейлиста для AI"""
    schema = {
        'daily_structure': [
            {
                'order': 1,
                'type': 'motivational',
                'category': 'intro',
                'description': 'Вступление и приветствие от тренера',
                'duration': '2 минуты',
                'trainer_dependent': True
            },
            {
                'order': 2,
                'type': 'exercise',
                'category': 'warmup',
                'count': 2,
                'description': 'Разминочные упражнения',
                'duration': '3.25 минуты каждое (3 подхода × 15 повторов)',
                'trainer_dependent': False
            },
            {
                'order': 3,
                'type': 'motivational',
                'category': 'after_warmup',
                'description': 'Мотивация после разминки',
                'duration': '2 минуты',
                'trainer_dependent': True
            },
            {
                'order': 4,
                'type': 'exercise',
                'category': 'main',
                'count': 5,
                'description': 'Основные силовые упражнения',
                'duration': '3.25 минуты каждое (3 подхода × 15 повторов)',
                'trainer_dependent': False
            },
            {
                'order': 5,
                'type': 'motivational',
                'category': 'after_main',
                'description': 'Мотивация после основных упражнений',
                'duration': '2 минуты',
                'trainer_dependent': True
            },
            {
                'order': 6,
                'type': 'exercise',
                'category': 'endurance',
                'count': 2,
                'description': 'Упражнения на сексуальную выносливость',
                'duration': '3.25 минуты каждое (3 подхода × 15 повторов)',
                'trainer_dependent': False
            },
            {
                'order': 7,
                'type': 'motivational',
                'category': 'motivating_speech',
                'description': 'Мотивирующий ролик тренера',
                'duration': '2 минуты',
                'trainer_dependent': True
            },
            {
                'order': 8,
                'type': 'exercise',
                'category': 'cooldown',
                'count': 2,
                'description': 'Упражнения на расслабление и растяжку',
                'duration': '3.25 минуты каждое (3 подхода × 15 повторов)',
                'trainer_dependent': False
            },
            {
                'order': 9,
                'type': 'motivational',
                'category': 'farewell',
                'description': 'Напутственное слово от тренера',
                'duration': '2 минуты',
                'trainer_dependent': True
            }
        ],
        'special_videos': {
            'weekly': {
                'frequency': 'Каждое воскресенье (дни 7, 14, 21)',
                'duration': '10 минут',
                'description': 'Еженедельное мотивационное видео'
            },
            'biweekly': {
                'frequency': 'Каждые 2 недели (дни 14, 28, 42)',
                'duration': '15 минут',
                'description': 'Двухнедельное прогресс-видео'
            },
            'final': {
                'frequency': 'Последний день курса',
                'duration': '10-15 минут',
                'description': 'Финальное поздравление'
            }
        },
        'rules': [
            'ЗАПРЕЩЕНО повторять упражнения в рамках одного дня',
            'ЗАПРЕЩЕНО повторять упражнения в первые 3 недели (21 день)',
            'В неделях 4-6 использовать только упражнения с оценкой ≥ 4 звезды',
            'Соблюдать баланс групп мышц в основных упражнениях',
            'Мотивационные видео должны соответствовать дню курса и архетипу тренера'
        ]
    }
    
    # Сохраняем схему
    schema_file = '/Users/alexbel/Desktop/AI Fitness Coach/prompts/playlist_schema.txt'
    
    with open(schema_file, 'w', encoding='utf-8') as f:
        f.write("# СХЕМА ЕЖЕДНЕВНОГО ПЛЕЙЛИСТА ДЛЯ AI\n")
        f.write("# 16 видео, общая длительность 45.8 минут\n\n")
        
        f.write("СТРУКТУРА ЕЖЕДНЕВНОГО ПЛЕЙЛИСТА:\n")
        f.write("=" * 60 + "\n\n")
        
        for item in schema['daily_structure']:
            f.write(f"{item['order']}. {item['type'].upper()}")
            if 'count' in item:
                f.write(f" ({item['count']} упражнения)")
            f.write(f" - {item['category']}\n")
            f.write(f"   Описание: {item['description']}\n")
            f.write(f"   Длительность: {item['duration']}\n")
            f.write(f"   От тренера: {'Да' if item['trainer_dependent'] else 'Нет'}\n\n")
        
        f.write("СПЕЦИАЛЬНЫЕ ВИДЕО:\n")
        f.write("=" * 30 + "\n\n")
        
        for video_type, info in schema['special_videos'].items():
            f.write(f"{video_type.upper()}:\n")
            f.write(f"  Частота: {info['frequency']}\n")
            f.write(f"  Длительность: {info['duration']}\n")
            f.write(f"  Описание: {info['description']}\n\n")
        
        f.write("СТРОГИЕ ПРАВИЛА:\n")
        f.write("=" * 20 + "\n\n")
        
        for i, rule in enumerate(schema['rules'], 1):
            f.write(f"{i}. {rule}\n")
    
    print(f"  ✅ Схема плейлиста сохранена в {schema_file}")

def main():
    """Основная функция категоризации"""
    print("🚀 КАТЕГОРИЗАЦИЯ УПРАЖНЕНИЙ ДЛЯ AI ПРОМПТОВ")
    print("=" * 70)
    
    try:
        # Категоризируем упражнения
        categories = categorize_exercises_by_names()
        
        # Валидируем результат
        validate_categories(categories)
        
        # Сохраняем списки по категориям
        save_categorized_lists(categories)
        
        # Создаем схему плейлиста
        create_playlist_schema()
        
        print(f"\n✅ КАТЕГОРИЗАЦИЯ ЗАВЕРШЕНА!")
        print("Созданы списки упражнений по категориям и схема плейлиста для AI.")
        
    except Exception as e:
        print(f"\n❌ Ошибка при категоризации: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()