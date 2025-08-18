#!/usr/bin/env python3
"""
Анализатор длительности видео для отбора подходящих файлов
Использует ffprobe для определения длительности видео
"""

import subprocess
import json
import os
import csv
from pathlib import Path

def get_video_duration(video_path):
    """Получить длительность видео в секундах используя ffprobe"""
    try:
        cmd = [
            'ffprobe', 
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            duration = float(data['format']['duration'])
            return duration
        else:
            return None
    except Exception as e:
        print(f"Ошибка при анализе {video_path}: {e}")
        return None

def categorize_by_duration(duration):
    """Категоризация видео по длительности"""
    if duration is None:
        return "unknown"
    elif duration <= 20:
        return "reminder"  # 10-20 сек - напоминания
    elif duration <= 40:
        return "instruction"  # 20-40 сек - инструкции  
    elif duration <= 60:
        return "technique"  # 30-60 сек - техника
    elif duration <= 300:  # 5 минут
        return "weekly"  # 2-5 мин - еженедельные
    else:
        return "final"  # 3-7+ мин - финальные

def analyze_trainer_videos(trainer_path, trainer_name):
    """Анализ видео одного тренера"""
    
    print(f"🔍 Анализируем {trainer_name}...")
    
    # Находим все mp4 файлы
    video_files = []
    for root, dirs, files in os.walk(trainer_path):
        for file in files:
            if file.lower().endswith('.mp4'):
                video_files.append(os.path.join(root, file))
    
    analysis_results = []
    categories = {
        "reminder": [],
        "instruction": [],
        "technique": [],
        "weekly": [],
        "final": [],
        "unknown": []
    }
    
    total_files = len(video_files)
    processed = 0
    
    for video_path in video_files:
        duration = get_video_duration(video_path)
        category = categorize_by_duration(duration)
        
        file_info = {
            "file_path": video_path,
            "file_name": os.path.basename(video_path),
            "duration_seconds": duration,
            "duration_formatted": f"{int(duration//60)}:{int(duration%60):02d}" if duration else "unknown",
            "category": category,
            "file_size": os.path.getsize(video_path) if os.path.exists(video_path) else 0
        }
        
        analysis_results.append(file_info)
        categories[category].append(file_info)
        
        processed += 1
        if processed % 50 == 0:
            print(f"  Обработано: {processed}/{total_files}")
    
    # Статистика
    stats = {
        "trainer": trainer_name,
        "total_videos": total_files,
        "categories": {cat: len(videos) for cat, videos in categories.items()},
        "avg_duration": sum(r['duration_seconds'] for r in analysis_results if r['duration_seconds']) / len([r for r in analysis_results if r['duration_seconds']]),
        "total_duration": sum(r['duration_seconds'] for r in analysis_results if r['duration_seconds'])
    }
    
    print(f"✅ {trainer_name} - найдено {total_files} видео:")
    for cat, count in stats['categories'].items():
        print(f"  {cat}: {count}")
    
    return {
        "stats": stats,
        "videos": analysis_results,
        "categories": categories
    }

def analyze_all_trainers():
    """Анализ всех тренеров"""
    
    trainers = {
        "trainer_1": "/Volumes/Z9/материалы для ai fitnes/trainer 1",
        "trainer_2": "/Volumes/Z9/материалы для ai fitnes/trainer 2", 
        "trainer_3": "/Volumes/Z9/материалы для ai fitnes/trainer 3",
        "long_videos": "/Volumes/Z9/материалы для ai fitnes/long and weekly videos"
    }
    
    all_results = {}
    
    for trainer_id, trainer_path in trainers.items():
        if os.path.exists(trainer_path):
            result = analyze_trainer_videos(trainer_path, trainer_id)
            all_results[trainer_id] = result
        else:
            print(f"❌ Путь не найден: {trainer_path}")
    
    return all_results

def create_selection_plan(analysis_results):
    """Создание плана отбора видео на основе анализа"""
    
    # Требования из анализа
    requirements = {
        "technique": 144,      # 144 упражнения × 1 техника
        "instruction": 432,    # 144 упражнения × 3 архетипа  
        "reminder": 432,       # 144 упражнения × 3 архетипа
        "weekly": 24,          # 3 архетипа × 8 недель
        "final": 3             # 3 архетипа
    }
    
    # Доступность по категориям
    available = {}
    for category in requirements.keys():
        available[category] = []
        for trainer_id, result in analysis_results.items():
            available[category].extend(result['categories'][category])
    
    selection_plan = {}
    
    for category, needed in requirements.items():
        available_count = len(available[category])
        
        if available_count >= needed:
            # Отбираем лучшие видео
            videos = available[category]
            
            # Сортируем по длительности (ближе к целевой)
            target_durations = {
                "technique": 45,    # 30-60 сек, цель 45
                "instruction": 30,  # 20-40 сек, цель 30
                "reminder": 15,     # 10-20 сек, цель 15
                "weekly": 180,      # 2-5 мин, цель 3 мин
                "final": 300        # 3-7 мин, цель 5 мин
            }
            
            target = target_durations[category]
            videos.sort(key=lambda x: abs(x['duration_seconds'] - target) if x['duration_seconds'] else float('inf'))
            
            selected = videos[:needed]
            selection_plan[category] = {
                "needed": needed,
                "available": available_count,
                "selected": selected,
                "status": "sufficient"
            }
        else:
            selection_plan[category] = {
                "needed": needed,
                "available": available_count,
                "selected": available[category],  # Берем все доступные
                "status": "insufficient"
            }
    
    return selection_plan

def save_analysis_results(analysis_results, selection_plan):
    """Сохранение результатов анализа"""
    
    # Сохраняем полный анализ
    output_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/VIDEO_DURATION_ANALYSIS.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "analysis_results": analysis_results,
            "selection_plan": selection_plan
        }, f, ensure_ascii=False, indent=2)
    
    # Создаем CSV для удобства
    csv_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/VIDEO_SELECTION_LIST.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Category', 'Original_Path', 'File_Name', 'Duration_Seconds', 'Duration_Formatted', 'New_Name_Pattern', 'Target_Folder'])
        
        for category, plan in selection_plan.items():
            for i, video in enumerate(plan['selected']):
                new_name_pattern = generate_new_name_pattern(category, i)
                target_folder = f"/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/{get_target_folder(category)}"
                
                writer.writerow([
                    category,
                    video['file_path'],
                    video['file_name'],
                    video['duration_seconds'],
                    video['duration_formatted'],
                    new_name_pattern,
                    target_folder
                ])
    
    # Создаем отчет
    create_selection_report(analysis_results, selection_plan)
    
    print(f"💾 Анализ сохранен: {output_file}")
    print(f"📊 CSV список: {csv_file}")

def generate_new_name_pattern(category, index):
    """Генерация шаблона нового имени"""
    
    patterns = {
        "technique": f"exercise_{index+1:03d}_technique_mod1.mp4",
        "instruction": f"exercise_{(index//3)+1:03d}_instruction_arch{(index%3)+1}_mod1.mp4",
        "reminder": f"exercise_{(index//3)+1:03d}_reminder_arch{(index%3)+1}_{(index%3)+1}.mp4",
        "weekly": f"weekly_arch{(index//8)+1}_week{(index%8)+1}.mp4",
        "final": f"final_arch{index+1}.mp4"
    }
    
    return patterns.get(category, f"{category}_{index+1}.mp4")

def get_target_folder(category):
    """Получить целевую папку для категории"""
    
    folders = {
        "technique": "exercises",
        "instruction": "instructions", 
        "reminder": "reminders",
        "weekly": "weekly",
        "final": "final"
    }
    
    return folders.get(category, "other")

def create_selection_report(analysis_results, selection_plan):
    """Создание отчета по отбору"""
    
    report = f"""# Отчет по анализу и отбору видео

## 📊 Анализ длительности видео

### Статистика по тренерам:
"""
    
    for trainer_id, result in analysis_results.items():
        stats = result['stats']
        report += f"""
#### {trainer_id}:
- Всего видео: {stats['total_videos']}
- Средняя длительность: {stats['avg_duration']:.1f} сек
- Общая длительность: {stats['total_duration']:.0f} сек ({stats['total_duration']/3600:.1f} часов)

Распределение по категориям:
"""
        for cat, count in stats['categories'].items():
            report += f"- {cat}: {count} видео\n"
    
    report += f"""
## 🎯 План отбора видео

"""
    
    for category, plan in selection_plan.items():
        status_emoji = "✅" if plan['status'] == 'sufficient' else "⚠️"
        report += f"""
### {status_emoji} {category.title()}
- Требуется: {plan['needed']} видео
- Доступно: {plan['available']} видео
- Отобрано: {len(plan['selected'])} видео
- Статус: {plan['status']}
"""
    
    report += f"""
## 📋 Следующие шаги

1. **Проверить ffprobe** - убедиться что установлен для анализа длительности
2. **Запустить отбор** - использовать CSV список для копирования и переименования
3. **Создать структуру** - скопировать отобранные видео в правильные папки
4. **Переименовать** - применить новые имена согласно системе именования
5. **Загрузить на Cloudflare** - подготовить к использованию в приложении

## ⚡ Автоматизация

Рекомендуется создать скрипт для:
- Массового копирования видео
- Автоматического переименования  
- Проверки целостности
- Создания JSON-конфигурации для приложения
"""
    
    report_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/VIDEO_SELECTION_REPORT.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📋 Отчет создан: {report_file}")

def main():
    """Основная функция"""
    
    print("🎬 Начинаем анализ видео...")
    
    # Проверяем наличие ffprobe
    try:
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
        print("✅ ffprobe найден")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ffprobe не найден. Установите ffmpeg/ffprobe для анализа длительности")
        print("Для macOS: brew install ffmpeg")
        return
    
    # Анализируем все видео
    analysis_results = analyze_all_trainers()
    
    # Создаем план отбора
    selection_plan = create_selection_plan(analysis_results)
    
    # Сохраняем результаты
    save_analysis_results(analysis_results, selection_plan)
    
    print("\n🎉 Анализ завершен!")
    print("📁 Проверьте файлы:")
    print("  - VIDEO_DURATION_ANALYSIS.json")
    print("  - VIDEO_SELECTION_LIST.csv") 
    print("  - VIDEO_SELECTION_REPORT.md")

if __name__ == '__main__':
    main()