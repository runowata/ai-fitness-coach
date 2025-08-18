#!/usr/bin/env python3
"""
ПРАВИЛЬНЫЙ отборщик видео: точно 616 видео
271 упражнений + 345 мотивационных = 616 видео
"""

import os
import shutil
import json
import pandas as pd
from datetime import datetime

def get_file_size_mb(file_path):
    """Получить размер файла в мегабайтах"""
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except:
        return 0

def collect_exercise_videos():
    """Собрать 271 видео упражнений из папки exercises"""
    
    exercise_folder = "/Volumes/Z9/материалы для ai fitnes/exercises"
    
    print(f"💪 Собираем 271 видео упражнений...")
    
    suitable_videos = []
    
    for root, dirs, files in os.walk(exercise_folder):
        for file in files:
            if file.lower().endswith('.mp4'):
                file_path = os.path.join(root, file)
                size_mb = get_file_size_mb(file_path)
                
                # Берем видео 1-5 минут (5-50 MB)
                if 5 <= size_mb <= 50:
                    suitable_videos.append({
                        "file_path": file_path,
                        "file_name": file,
                        "size_mb": round(size_mb, 2)
                    })
    
    # Сортируем по размеру, берем лучшие
    suitable_videos.sort(key=lambda x: abs(x["size_mb"] - 20))  # Предпочитаем ~20MB
    
    # Берем ровно 271 видео
    selected = suitable_videos[:271]
    
    print(f"✅ Отобрано {len(selected)} видео упражнений из {len(suitable_videos)} доступных")
    
    return selected

def collect_trainer_videos():
    """Собрать 345 видео от тренеров"""
    
    trainers = {
        "bro": "/Volumes/Z9/материалы для ai fitnes/trainer 1",
        "sergeant": "/Volumes/Z9/материалы для ai fitnes/trainer 2", 
        "intellectual": "/Volumes/Z9/материалы для ai fitnes/trainer 3"
    }
    
    print(f"🎬 Собираем 345 видео от тренеров...")
    
    trainer_videos = {}
    
    for archetype, path in trainers.items():
        videos = []
        
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.lower().endswith('.mp4'):
                    file_path = os.path.join(root, file)
                    size_mb = get_file_size_mb(file_path)
                    
                    videos.append({
                        "file_path": file_path,
                        "file_name": file,
                        "size_mb": round(size_mb, 2),
                        "archetype": archetype
                    })
        
        # Сортируем по размеру
        videos.sort(key=lambda x: x["size_mb"])
        trainer_videos[archetype] = videos
        
        print(f"  {archetype}: {len(videos)} видео доступно")
    
    return trainer_videos

def collect_long_videos():
    """Собрать длинные видео для еженедельных/финальных"""
    
    long_folder = "/Volumes/Z9/материалы для ai fitnes/long and weekly videos"
    
    print(f"📹 Собираем длинные видео...")
    
    long_videos = []
    
    for root, dirs, files in os.walk(long_folder):
        for file in files:
            if file.lower().endswith('.mp4'):
                file_path = os.path.join(root, file)
                size_mb = get_file_size_mb(file_path)
                
                # Для длинных видео берем от 30MB (примерно 3+ минуты)
                if size_mb >= 30:
                    long_videos.append({
                        "file_path": file_path,
                        "file_name": file,
                        "size_mb": round(size_mb, 2)
                    })
    
    # Сортируем по размеру (предпочитаем средние размеры)
    long_videos.sort(key=lambda x: abs(x["size_mb"] - 50))
    
    print(f"✅ Найдено {len(long_videos)} длинных видео")
    
    return long_videos

def create_exercise_mapping(exercise_videos):
    """Создать маппинг 271 упражнения"""
    
    # Загружаем старую базу упражнений (271 упражнение)
    excel_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/COMPLETE_EXERCISES_DATABASE.xlsx'
    
    try:
        df = pd.read_excel(excel_file, sheet_name='All_Exercises')
        exercises = df.to_dict('records')[:271]  # Берем ровно 271
        print(f"📋 Загружено {len(exercises)} упражнений из старой базы")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки, создаем тестовые упражнения: {e}")
        # Создаем структуру по категориям
        exercises = []
        categories = [
            ("warmup", "Разминка", 42),
            ("main", "Основные", 145),
            ("sexual_endurance", "Сексуальная выносливость", 42),
            ("relaxation", "Расслабление", 42)
        ]
        
        ex_id = 1
        for category, category_ru, count in categories:
            for i in range(count):
                exercises.append({
                    "id": ex_id,
                    "slug": f"{category}_{i+1:02d}",
                    "name_en": f"{category.replace('_', ' ').title()} {i+1}",
                    "name_ru": f"{category_ru} {i+1}",
                    "category": category,
                    "category_ru": category_ru,
                    "file_name": f"{category}_{i+1:02d}_technique_m01.mp4"
                })
                ex_id += 1
    
    # Создаем маппинг
    exercise_mapping = []
    
    for i, exercise in enumerate(exercises):
        video = exercise_videos[i] if i < len(exercise_videos) else exercise_videos[i % len(exercise_videos)]
        
        file_name = exercise.get("file_name", f"{exercise.get('slug', f'exercise_{i+1}')}_technique_m01.mp4")
        
        exercise_mapping.append({
            "exercise_id": exercise.get("id", i+1),
            "exercise_slug": exercise.get("slug", f"exercise_{i+1}"),
            "exercise_name": exercise.get("name_en", f"Exercise {i+1}"),
            "exercise_name_ru": exercise.get("name_ru", f"Упражнение {i+1}"),
            "category": exercise.get("category", "unknown"),
            "category_ru": exercise.get("category_ru", "Неизвестно"),
            "original_path": video["file_path"],
            "original_name": video["file_name"],
            "new_name": file_name,
            "size_mb": video["size_mb"],
            "target_path": f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/exercises/{file_name}",
            "cloudflare_url": f"https://ai-fitness-media.r2.cloudflarestorage.com/videos/exercises/{file_name}"
        })
    
    print(f"✅ Создан маппинг для {len(exercise_mapping)} упражнений")
    
    return exercise_mapping

def create_motivational_mapping(trainer_videos, long_videos):
    """Создать маппинг 345 мотивационных видео"""
    
    archetypes = ["bro", "sergeant", "intellectual"]
    
    motivational_mapping = []
    
    # Короткие мотивационные видео (315 видео: 63 × 5 типов)
    short_types = [
        ("intro", "Вступление и приветствие"),
        ("warmup_motivation", "Мотивация после разминки"),
        ("main_motivation", "Мотивация после основных"),
        ("trainer_speech", "Мотивирующий ролик тренера"),
        ("closing", "Напутственное слово")
    ]
    
    video_index = 0
    
    # 1. Короткие мотивационные (315 видео)
    for video_type, description in short_types:
        for week in range(1, 22):  # 21 день программы
            for archetype in archetypes:
                # Выбираем видео от соответствующего тренера
                available_videos = trainer_videos.get(archetype, [])
                
                if available_videos:
                    video = available_videos[video_index % len(available_videos)]
                    
                    new_name = f"{video_type}_{archetype}_day{week:02d}.mp4"
                    
                    motivational_mapping.append({
                        "type": video_type,
                        "description": description,
                        "archetype": archetype,
                        "day": week,
                        "original_path": video["file_path"],
                        "original_name": video["file_name"],
                        "new_name": new_name,
                        "size_mb": video["size_mb"],
                        "target_path": f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/motivation/{new_name}",
                        "cloudflare_url": f"https://ai-fitness-media.r2.cloudflarestorage.com/videos/motivation/{new_name}"
                    })
                    
                    video_index += 1
    
    # 2. Еженедельные длинные (18 видео)
    long_index = 0
    for week in range(1, 7):  # 6 недель
        for archetype in archetypes:
            video = long_videos[long_index % len(long_videos)]
            
            new_name = f"weekly_{archetype}_week{week}.mp4"
            
            motivational_mapping.append({
                "type": "weekly",
                "description": "Еженедельные длинные (10 мин)",
                "archetype": archetype,
                "week": week,
                "original_path": video["file_path"],
                "original_name": video["file_name"],
                "new_name": new_name,
                "size_mb": video["size_mb"],
                "target_path": f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/weekly/{new_name}",
                "cloudflare_url": f"https://ai-fitness-media.r2.cloudflarestorage.com/videos/weekly/{new_name}"
            })
            
            long_index += 1
    
    # 3. Двухнедельные прогресс-видео (9 видео)
    for progress_num in range(1, 4):  # 3 раза
        for archetype in archetypes:
            video = long_videos[long_index % len(long_videos)]
            
            new_name = f"progress_{archetype}_{progress_num}.mp4"
            
            motivational_mapping.append({
                "type": "progress",
                "description": "Двухнедельные прогресс-видео",
                "archetype": archetype,
                "progress_number": progress_num,
                "original_path": video["file_path"],
                "original_name": video["file_name"],
                "new_name": new_name,
                "size_mb": video["size_mb"],
                "target_path": f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/progress/{new_name}",
                "cloudflare_url": f"https://ai-fitness-media.r2.cloudflarestorage.com/videos/progress/{new_name}"
            })
            
            long_index += 1
    
    # 4. Финальные видео (3 видео)
    for archetype in archetypes:
        video = long_videos[long_index % len(long_videos)]
        
        new_name = f"final_{archetype}.mp4"
        
        motivational_mapping.append({
            "type": "final",
            "description": "Финальное видео курса",
            "archetype": archetype,
            "original_path": video["file_path"],
            "original_name": video["file_name"],
            "new_name": new_name,
            "size_mb": video["size_mb"],
            "target_path": f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/final/{new_name}",
            "cloudflare_url": f"https://ai-fitness-media.r2.cloudflarestorage.com/videos/final/{new_name}"
        })
        
        long_index += 1
    
    print(f"✅ Создан маппинг для {len(motivational_mapping)} мотивационных видео")
    
    # Проверяем количество по типам
    type_counts = {}
    for item in motivational_mapping:
        video_type = item["type"]
        type_counts[video_type] = type_counts.get(video_type, 0) + 1
    
    print(f"📊 Распределение мотивационных видео:")
    for video_type, count in type_counts.items():
        print(f"  {video_type}: {count}")
    
    return motivational_mapping

def copy_all_616_videos(exercise_mapping, motivational_mapping):
    """Копирование всех 616 видео"""
    
    # Создаем папки
    folders = ["exercises", "motivation", "weekly", "progress", "final"]
    for folder in folders:
        folder_path = f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/{folder}"
        os.makedirs(folder_path, exist_ok=True)
    
    all_videos = exercise_mapping + motivational_mapping
    total_files = len(all_videos)
    
    print(f"\n🚀 Копируем {total_files} видео...")
    print(f"  💪 Упражнения: {len(exercise_mapping)}")
    print(f"  🎬 Мотивационные: {len(motivational_mapping)}")
    
    copied_count = 0
    error_count = 0
    start_time = datetime.now()
    
    for i, video in enumerate(all_videos):
        try:
            source = video["original_path"]
            target = video["target_path"]
            
            if not os.path.exists(source):
                print(f"⚠️ Файл не найден: {source}")
                error_count += 1
                continue
            
            # Копируем файл
            shutil.copy2(source, target)
            copied_count += 1
            
            # Показываем прогресс каждые 25 файлов
            if (i + 1) % 25 == 0 or (i + 1) == total_files:
                progress = (i + 1) / total_files * 100
                elapsed = datetime.now() - start_time
                eta = elapsed * (total_files / (i + 1)) - elapsed
                
                print(f"  📦 Прогресс: {i+1}/{total_files} ({progress:.1f}%) | "
                      f"✅ {copied_count} | ❌ {error_count} | ETA: {eta}")
            
        except Exception as e:
            print(f"❌ Ошибка: {video['original_name']} - {e}")
            error_count += 1
    
    total_time = datetime.now() - start_time
    
    print(f"\n🎉 КОПИРОВАНИЕ ЗАВЕРШЕНО!")
    print(f"⏱️  Время: {total_time}")
    print(f"✅ Успешно: {copied_count}")
    print(f"❌ Ошибок: {error_count}")
    print(f"📊 Успешность: {copied_count/(copied_count+error_count)*100:.1f}%")
    
    return copied_count, error_count

def save_616_config(exercise_mapping, motivational_mapping):
    """Сохранить конфигурацию для 616 видео"""
    
    total_videos = len(exercise_mapping) + len(motivational_mapping)
    
    config = {
        "system_info": {
            "version": "616 Video System",
            "created": datetime.now().isoformat(),
            "total_videos": total_videos,
            "exercise_videos": len(exercise_mapping),
            "motivational_videos": len(motivational_mapping)
        },
        "video_structure": {
            "exercises": {
                "count": len(exercise_mapping),
                "categories": {
                    "warmup": 42,
                    "main": 145,
                    "sexual_endurance": 42,
                    "relaxation": 42
                }
            },
            "motivational": {
                "count": len(motivational_mapping),
                "types": {
                    "intro": 63,
                    "warmup_motivation": 63,
                    "main_motivation": 63,
                    "trainer_speech": 63,
                    "closing": 63,
                    "weekly": 18,
                    "progress": 9,
                    "final": 3
                }
            }
        },
        "exercises_by_category": {},
        "motivational_by_type": {},
        "cloudflare_base": "https://ai-fitness-media.r2.cloudflarestorage.com/videos/"
    }
    
    # Группируем упражнения по категориям
    for video in exercise_mapping:
        category = video["category"]
        if category not in config["exercises_by_category"]:
            config["exercises_by_category"][category] = []
        config["exercises_by_category"][category].append(video)
    
    # Группируем мотивационные по типам
    for video in motivational_mapping:
        video_type = video["type"]
        if video_type not in config["motivational_by_type"]:
            config["motivational_by_type"][video_type] = []
        config["motivational_by_type"][video_type].append(video)
    
    # Сохраняем конфигурацию
    config_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/SYSTEM_616_VIDEOS.json'
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    # Сохраняем CSV
    exercise_df = pd.DataFrame(exercise_mapping)
    exercise_csv = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/EXERCISES_271_VIDEOS.csv'
    exercise_df.to_csv(exercise_csv, index=False, encoding='utf-8')
    
    motivational_df = pd.DataFrame(motivational_mapping)
    motivational_csv = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/MOTIVATIONAL_345_VIDEOS.csv'
    motivational_df.to_csv(motivational_csv, index=False, encoding='utf-8')
    
    print(f"\n💾 Конфигурация сохранена:")
    print(f"  🔧 {config_file}")
    print(f"  💪 {exercise_csv}")
    print(f"  🎬 {motivational_csv}")
    
    return config

def main():
    """Основная функция"""
    
    print("🎯 ТОЧНО 616 ВИДЕО для AI FITNESS COACH")
    print("=" * 50)
    print("💪 Упражнения: 271 видео (42+145+42+42)")
    print("🎬 Мотивационные: 345 видео (315 коротких + 30 длинных)")
    print("🎯 ИТОГО: 616 видео")
    print()
    
    # 1. Собираем видео упражнений
    print("📂 Шаг 1: Сбор 271 видео упражнений...")
    exercise_videos = collect_exercise_videos()
    
    # 2. Собираем видео тренеров
    print("\n🎬 Шаг 2: Сбор видео тренеров...")
    trainer_videos = collect_trainer_videos()
    
    # 3. Собираем длинные видео
    print("\n📹 Шаг 3: Сбор длинных видео...")
    long_videos = collect_long_videos()
    
    # 4. Создаем маппинг упражнений
    print("\n💪 Шаг 4: Создание маппинга 271 упражнения...")
    exercise_mapping = create_exercise_mapping(exercise_videos)
    
    # 5. Создаем маппинг мотивационных
    print("\n🎬 Шаг 5: Создание маппинга 345 мотивационных...")
    motivational_mapping = create_motivational_mapping(trainer_videos, long_videos)
    
    # 6. Сохраняем конфигурацию
    print("\n💾 Шаг 6: Сохранение конфигурации...")
    config = save_616_config(exercise_mapping, motivational_mapping)
    
    # 7. Копируем файлы
    print("\n📁 Шаг 7: Копирование 616 файлов...")
    copied, errors = copy_all_616_videos(exercise_mapping, motivational_mapping)
    
    # Итоговая статистика
    total_size_gb = sum(v["size_mb"] for v in exercise_mapping + motivational_mapping) / 1024
    
    print(f"\n🎉 СИСТЕМА 616 ВИДЕО ГОТОВА!")
    print(f"📊 Создано:")
    print(f"  💪 Упражнения: {len(exercise_mapping)}")
    print(f"  🎬 Мотивационные: {len(motivational_mapping)}")
    print(f"  🎯 ВСЕГО: {len(exercise_mapping) + len(motivational_mapping)}")
    print(f"")
    print(f"💾 Размер: ~{total_size_gb:.1f} GB")
    print(f"✅ Скопировано: {copied}")
    print(f"❌ Ошибок: {errors}")
    print(f"")
    print(f"🔗 Готово для Cloudflare R2!")
    print(f"🤖 Готово для ChatGPT!")

if __name__ == '__main__':
    main()