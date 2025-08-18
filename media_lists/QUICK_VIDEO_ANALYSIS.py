#!/usr/bin/env python3
"""
Быстрый анализ видео из папки exercises без копирования
"""

import os
import json
import pandas as pd

def get_file_size_mb(file_path):
    """Получить размер файла в мегабайтах"""
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except:
        return 0

def is_suitable_for_exercise(size_mb):
    """Проверить подходит ли видео для упражнения (1-5 минут)"""
    return 5 <= size_mb <= 50

def quick_analysis():
    """Быстрый анализ без копирования"""
    
    exercise_folder = "/Volumes/Z9/материалы для ai fitnes/exercises"
    
    print(f"🔍 Быстрый анализ папки exercises...")
    
    suitable_videos = []
    total_scanned = 0
    total_size_gb = 0
    
    for root, dirs, files in os.walk(exercise_folder):
        for file in files:
            if file.lower().endswith('.mp4'):
                file_path = os.path.join(root, file)
                size_mb = get_file_size_mb(file_path)
                total_scanned += 1
                total_size_gb += size_mb / 1024
                
                if is_suitable_for_exercise(size_mb):
                    rel_path = os.path.relpath(root, exercise_folder)
                    
                    suitable_videos.append({
                        "file_path": file_path,
                        "file_name": file,
                        "folder": rel_path if rel_path != "." else "root",
                        "size_mb": round(size_mb, 2)
                    })
                
                if total_scanned % 200 == 0:
                    print(f"  Просканировано: {total_scanned}, найдено: {len(suitable_videos)}")
    
    print(f"\n✅ Анализ завершен:")
    print(f"  📊 Всего видео: {total_scanned}")
    print(f"  💾 Общий размер: {total_size_gb:.1f} GB")
    print(f"  🎯 Подходящих (1-5 мин): {len(suitable_videos)}")
    print(f"  📈 Процент подходящих: {len(suitable_videos)/total_scanned*100:.1f}%")
    
    if len(suitable_videos) >= 144:
        print(f"  ✅ ДОСТАТОЧНО для всех 144 упражнений!")
        surplus = len(suitable_videos) - 144
        print(f"  📈 Запас: {surplus} дополнительных видео")
    else:
        shortage = 144 - len(suitable_videos)
        print(f"  ⚠️ НЕДОСТАТОК: не хватает {shortage} видео")
    
    # Сохраняем список для дальнейшего использования
    result = {
        "analysis_summary": {
            "total_videos": total_scanned,
            "total_size_gb": round(total_size_gb, 1),
            "suitable_videos": len(suitable_videos),
            "suitable_percentage": round(len(suitable_videos)/total_scanned*100, 1),
            "enough_for_144": len(suitable_videos) >= 144,
            "surplus_or_shortage": len(suitable_videos) - 144
        },
        "suitable_videos": suitable_videos[:200]  # Сохраняем только первые 200 для примера
    }
    
    output_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/QUICK_VIDEO_ANALYSIS.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Анализ сохранен: {output_file}")
    
    # Показываем примеры найденных видео
    print(f"\n📋 Примеры подходящих видео:")
    for i, video in enumerate(suitable_videos[:10]):
        print(f"  {i+1}. {video['file_name']} ({video['size_mb']} MB) - {video['folder']}")
    
    return result

if __name__ == '__main__':
    quick_analysis()