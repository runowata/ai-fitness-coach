#!/usr/bin/env python3
"""
Простой отборщик видео для AI Fitness Coach
Использует размер файла как приблизительный индикатор длительности
"""

import os
import shutil
import json
import pandas as pd
from pathlib import Path

def get_file_size_mb(file_path):
    """Получить размер файла в мегабайтах"""
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except:
        return 0

def categorize_by_file_size(size_mb):
    """Категоризация по размеру файла (приблизительная оценка длительности)"""
    if size_mb < 5:
        return "reminder"    # Маленькие файлы - короткие видео
    elif size_mb < 15:
        return "instruction" # Средние файлы - инструкции
    elif size_mb < 30:
        return "technique"   # Большие файлы - техника
    elif size_mb < 100:
        return "weekly"      # Очень большие - еженедельные
    else:
        return "final"       # Огромные - финальные

def analyze_videos_by_size():
    """Анализ видео по размеру файлов"""
    
    trainers = {
        "trainer_1": {
            "path": "/Volumes/Z9/материалы для ai fitnes/trainer 1",
            "archetype": "bro",
            "model": "mod1"
        },
        "trainer_2": {
            "path": "/Volumes/Z9/материалы для ai fitnes/trainer 2",
            "archetype": "sergeant", 
            "model": "mod2"
        },
        "trainer_3": {
            "path": "/Volumes/Z9/материалы для ai fitnes/trainer 3",
            "archetype": "intellectual",
            "model": "mod3"
        },
        "long_videos": {
            "path": "/Volumes/Z9/материалы для ai fitnes/long and weekly videos",
            "archetype": "mixed",
            "model": "various"
        }
    }
    
    analysis = {}
    
    for trainer_id, info in trainers.items():
        print(f"🔍 Анализируем {trainer_id}...")
        
        videos = []
        trainer_path = info["path"]
        
        # Находим все mp4 файлы
        for root, dirs, files in os.walk(trainer_path):
            for file in files:
                if file.lower().endswith('.mp4'):
                    file_path = os.path.join(root, file)
                    size_mb = get_file_size_mb(file_path)
                    category = categorize_by_file_size(size_mb)
                    
                    videos.append({
                        "file_path": file_path,
                        "file_name": file,
                        "size_mb": round(size_mb, 2),
                        "category": category,
                        "trainer": trainer_id,
                        "archetype": info["archetype"],
                        "model": info["model"]
                    })
        
        # Группируем по категориям
        categories = {}
        for video in videos:
            cat = video["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(video)
        
        analysis[trainer_id] = {
            "info": info,
            "videos": videos,
            "categories": categories,
            "total_count": len(videos),
            "total_size_gb": sum(v["size_mb"] for v in videos) / 1024
        }
        
        print(f"  Найдено {len(videos)} видео, {analysis[trainer_id]['total_size_gb']:.1f} GB")
        for cat, vids in categories.items():
            print(f"    {cat}: {len(vids)} видео")
    
    return analysis

def select_videos_for_phase1(analysis):
    """Отбор видео для Фазы 1 - базовая техника упражнений"""
    
    # Загружаем список упражнений из новой базы
    excel_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/MODERN_EXERCISES_DATABASE_2025.xlsx'
    
    try:
        df = pd.read_excel(excel_file, sheet_name='All_Modern_Exercises')
        exercises = df.to_dict('records')
        print(f"📋 Загружено {len(exercises)} упражнений из базы")
    except Exception as e:
        print(f"❌ Ошибка загрузки упражнений: {e}")
        # Создаем тестовый список
        exercises = [{"slug": f"exercise_{i+1:03d}", "name_en": f"Exercise {i+1}"} for i in range(144)]
    
    # Отбираем видео для техники (trainer_1, категория technique)
    technique_videos = []
    if "trainer_1" in analysis:
        available_technique = analysis["trainer_1"]["categories"].get("technique", [])
        
        # Сортируем по размеру (предпочитаем средние размеры для техники)
        available_technique.sort(key=lambda x: abs(x["size_mb"] - 20))  # Целевой размер ~20MB
        
        # Отбираем нужное количество
        needed = min(len(exercises), len(available_technique))
        technique_videos = available_technique[:needed]
        
        print(f"✅ Отобрано {len(technique_videos)} видео для техники упражнений")
    
    # Создаем маппинг упражнение -> видео
    exercise_video_mapping = []
    for i, exercise in enumerate(exercises[:len(technique_videos)]):
        video = technique_videos[i]
        new_name = f"{exercise['slug']}_technique_mod1.mp4"
        
        exercise_video_mapping.append({
            "exercise_slug": exercise["slug"],
            "exercise_name": exercise.get("name_en", f"Exercise {i+1}"),
            "original_path": video["file_path"],
            "original_name": video["file_name"],
            "new_name": new_name,
            "size_mb": video["size_mb"],
            "target_path": f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/exercises/{new_name}",
            "cloudflare_url": f"https://ai-fitness-media.r2.cloudflarestorage.com/videos/exercises/{new_name}"
        })
    
    return exercise_video_mapping

def copy_and_rename_phase1(mapping):
    """Копирование и переименование видео для Фазы 1"""
    
    print(f"📁 Начинаем копирование {len(mapping)} видео...")
    
    # Создаем папку если не существует
    target_dir = "/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/exercises"
    os.makedirs(target_dir, exist_ok=True)
    
    success_count = 0
    error_count = 0
    
    for item in mapping:
        try:
            source = item["original_path"]
            target = item["target_path"]
            
            # Копируем файл
            shutil.copy2(source, target)
            success_count += 1
            
            if success_count % 20 == 0:
                print(f"  Скопировано: {success_count}/{len(mapping)}")
                
        except Exception as e:
            print(f"❌ Ошибка копирования {item['original_name']}: {e}")
            error_count += 1
    
    print(f"✅ Копирование завершено: {success_count} успешно, {error_count} ошибок")
    
    return success_count, error_count

def select_motivational_videos(analysis):
    """Отбор мотивационных видео (еженедельные и финальные)"""
    
    motivational_mapping = []
    
    # Еженедельные видео (24 видео: 3 архетипа × 8 недель)
    long_videos = analysis.get("long_videos", {}).get("categories", {})
    weekly_candidates = long_videos.get("weekly", []) + long_videos.get("final", [])
    
    if weekly_candidates:
        # Сортируем по размеру (предпочитаем средние размеры)
        weekly_candidates.sort(key=lambda x: abs(x["size_mb"] - 50))  # Целевой размер ~50MB
        
        archetypes = ["bro", "sergeant", "intellectual"]
        
        # Еженедельные видео
        video_index = 0
        for week in range(1, 9):  # 8 недель
            for archetype in archetypes:
                if video_index < len(weekly_candidates):
                    video = weekly_candidates[video_index]
                    new_name = f"weekly_{archetype}_week{week}.mp4"
                    
                    motivational_mapping.append({
                        "type": "weekly",
                        "archetype": archetype,
                        "week": week,
                        "original_path": video["file_path"],
                        "original_name": video["file_name"],
                        "new_name": new_name,
                        "size_mb": video["size_mb"],
                        "target_path": f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/weekly/{new_name}",
                        "cloudflare_url": f"https://ai-fitness-media.r2.cloudflarestorage.com/videos/weekly/{new_name}"
                    })
                    video_index += 1
        
        # Финальные видео (3 видео: по одному на архетип)
        for i, archetype in enumerate(archetypes):
            if video_index + i < len(weekly_candidates):
                video = weekly_candidates[video_index + i]
                new_name = f"final_{archetype}.mp4"
                
                motivational_mapping.append({
                    "type": "final",
                    "archetype": archetype,
                    "original_path": video["file_path"],
                    "original_name": video["file_name"], 
                    "new_name": new_name,
                    "size_mb": video["size_mb"],
                    "target_path": f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/final/{new_name}",
                    "cloudflare_url": f"https://ai-fitness-media.r2.cloudflarestorage.com/videos/final/{new_name}"
                })
    
    print(f"🎯 Отобрано {len(motivational_mapping)} мотивационных видео")
    return motivational_mapping

def copy_motivational_videos(mapping):
    """Копирование мотивационных видео"""
    
    print(f"🎬 Копируем мотивационные видео...")
    
    # Создаем папки
    for folder in ["weekly", "final"]:
        os.makedirs(f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/{folder}", exist_ok=True)
    
    success_count = 0
    error_count = 0
    
    for item in mapping:
        try:
            source = item["original_path"]
            target = item["target_path"]
            
            shutil.copy2(source, target)
            success_count += 1
            
        except Exception as e:
            print(f"❌ Ошибка копирования {item['original_name']}: {e}")
            error_count += 1
    
    print(f"✅ Мотивационные видео: {success_count} успешно, {error_count} ошибок")
    return success_count, error_count

def save_mapping_results(exercise_mapping, motivational_mapping):
    """Сохранение результатов маппинга"""
    
    # Полный результат
    result = {
        "phase_1_exercises": exercise_mapping,
        "motivational_videos": motivational_mapping,
        "summary": {
            "total_exercise_videos": len(exercise_mapping),
            "total_motivational_videos": len(motivational_mapping),
            "total_videos": len(exercise_mapping) + len(motivational_mapping),
            "total_size_gb": sum(item["size_mb"] for item in exercise_mapping + motivational_mapping) / 1024
        }
    }
    
    # Сохраняем JSON
    json_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/VIDEO_MAPPING_PHASE1.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # Создаем CSV для упражнений
    exercise_df = pd.DataFrame(exercise_mapping)
    exercise_csv = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/EXERCISE_VIDEOS_PHASE1.csv'
    exercise_df.to_csv(exercise_csv, index=False, encoding='utf-8')
    
    # Создаем CSV для мотивационных
    motivational_df = pd.DataFrame(motivational_mapping)
    motivational_csv = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/MOTIVATIONAL_VIDEOS.csv'
    motivational_df.to_csv(motivational_csv, index=False, encoding='utf-8')
    
    # Создаем конфигурацию для ChatGPT
    chatgpt_config = create_chatgpt_config(exercise_mapping, motivational_mapping)
    config_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/CHATGPT_VIDEO_CONFIG.json'
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(chatgpt_config, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Маппинг сохранен:")
    print(f"  📄 {json_file}")
    print(f"  📊 {exercise_csv}")
    print(f"  🎬 {motivational_csv}")
    print(f"  🤖 {config_file}")
    
    return result

def create_chatgpt_config(exercise_mapping, motivational_mapping):
    """Создание конфигурации для ChatGPT"""
    
    # Группируем упражнения по категориям
    exercises_by_category = {}
    for item in exercise_mapping:
        # Пытаемся определить категорию из slug
        slug = item["exercise_slug"]
        if "prep" in slug or "activation" in slug:
            category = "movement_prep"
        elif "push" in slug or "pull" in slug or "squat" in slug:
            category = "fundamental_patterns"
        elif "jump" in slug or "explosive" in slug:
            category = "power_explosive"
        elif "beast" in slug or "crab" in slug or "flow" in slug:
            category = "primal_flow"
        elif "corrective" in slug or "mobility" in slug:
            category = "corrective_therapeutic"
        elif "mindful" in slug or "breathing" in slug:
            category = "mindful_movement"
        elif "recovery" in slug or "relaxation" in slug:
            category = "recovery_regeneration"
        else:
            category = "fundamental_patterns"  # по умолчанию
            
        if category not in exercises_by_category:
            exercises_by_category[category] = []
        exercises_by_category[category].append(item)
    
    # Мотивационные видео по архетипам
    weekly_by_archetype = {}
    final_by_archetype = {}
    
    for item in motivational_mapping:
        if item["type"] == "weekly":
            archetype = item["archetype"]
            if archetype not in weekly_by_archetype:
                weekly_by_archetype[archetype] = []
            weekly_by_archetype[archetype].append(item)
        elif item["type"] == "final":
            final_by_archetype[item["archetype"]] = item
    
    config = {
        "system_info": {
            "version": "1.0",
            "phase": "Phase 1 - Basic Technique Videos",
            "total_exercises": len(exercise_mapping),
            "total_motivational": len(motivational_mapping)
        },
        "exercises": {
            "by_category": exercises_by_category,
            "by_slug": {item["exercise_slug"]: item for item in exercise_mapping}
        },
        "motivational": {
            "weekly_by_archetype": weekly_by_archetype,
            "final_by_archetype": final_by_archetype
        },
        "archetypes": {
            "bro": {
                "name": "Дружелюбный тренер-приятель",
                "tone": "Неформальный, поддерживающий",
                "examples": ["Давай, братан!", "Ты можешь!", "Отличная работа!"]
            },
            "sergeant": {
                "name": "Строгий тренер-сержант", 
                "tone": "Четкий, командный",
                "examples": ["Выполняй!", "Без поблажек!", "Дисциплина!"]
            },
            "intellectual": {
                "name": "Мудрый тренер-интеллектуал",
                "tone": "Спокойный, образовательный",
                "examples": ["Помни о технике", "Научно доказано", "Осознанное движение"]
            }
        },
        "usage_examples": {
            "get_exercise_video": "exercise_mapping['quality-push-up']['cloudflare_url']",
            "get_weekly_motivation": "weekly_by_archetype['bro'][week-1]['cloudflare_url']",
            "get_final_congratulation": "final_by_archetype['intellectual']['cloudflare_url']"
        }
    }
    
    return config

def main():
    """Основная функция"""
    
    print("🎬 Запуск простого отборщика видео для AI Fitness Coach")
    print("=" * 60)
    
    # 1. Анализируем видео по размеру
    print("\n📊 Шаг 1: Анализ видео по размеру файлов...")
    analysis = analyze_videos_by_size()
    
    # 2. Отбираем видео для Фазы 1 (техника упражнений)
    print("\n🎯 Шаг 2: Отбор видео для техники упражнений...")
    exercise_mapping = select_videos_for_phase1(analysis)
    
    # 3. Отбираем мотивационные видео
    print("\n🎬 Шаг 3: Отбор мотивационных видео...")
    motivational_mapping = select_motivational_videos(analysis)
    
    # 4. Сохраняем результаты
    print("\n💾 Шаг 4: Сохранение результатов...")
    results = save_mapping_results(exercise_mapping, motivational_mapping)
    
    # 5. Копируем файлы (автоматически)
    print("\n📁 Шаг 5: Копирование и переименование файлов...")
    
    print("🚀 Автоматическое копирование файлов...")
    exercise_success, exercise_errors = copy_and_rename_phase1(exercise_mapping)
    motivational_success, motivational_errors = copy_motivational_videos(motivational_mapping)
    
    print(f"\n🎉 Завершено!")
    print(f"📊 Упражнения: {exercise_success} успешно, {exercise_errors} ошибок")
    print(f"🎬 Мотивационные: {motivational_success} успешно, {motivational_errors} ошибок")
    
    print(f"\n📁 Структура создана в: /Volumes/Z9/AI_FITNESS_COACH_VIDEOS/")
    print(f"📊 Всего подготовлено: {results['summary']['total_videos']} видео")
    print(f"💾 Общий размер: {results['summary']['total_size_gb']:.1f} GB")

if __name__ == '__main__':
    main()