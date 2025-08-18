#!/usr/bin/env python3
"""
Удаление дубликатов и лишних видео
Оставляем только 616 видео согласно утвержденной схеме
"""

import os
import pandas as pd
import json
from datetime import datetime

def load_correct_video_lists():
    """Загрузить списки правильных видео из CSV файлов"""
    
    correct_videos = {
        "exercises": [],
        "motivational": []
    }
    
    # Загружаем список 271 упражнения
    try:
        exercises_df = pd.read_csv('/Users/alexbel/Desktop/AI Fitness Coach/media_lists/EXERCISES_271_VIDEOS.csv')
        for _, row in exercises_df.iterrows():
            correct_videos["exercises"].append({
                "new_name": row["new_name"],
                "target_path": row["target_path"]
            })
        print(f"✅ Загружено {len(correct_videos['exercises'])} правильных упражнений")
    except Exception as e:
        print(f"❌ Ошибка загрузки упражнений: {e}")
        return None
    
    # Загружаем список 345 мотивационных
    try:
        motivational_df = pd.read_csv('/Users/alexbel/Desktop/AI Fitness Coach/media_lists/MOTIVATIONAL_345_VIDEOS.csv')
        for _, row in motivational_df.iterrows():
            correct_videos["motivational"].append({
                "new_name": row["new_name"],
                "target_path": row["target_path"]
            })
        print(f"✅ Загружено {len(correct_videos['motivational'])} правильных мотивационных")
    except Exception as e:
        print(f"❌ Ошибка загрузки мотивационных: {e}")
        return None
    
    return correct_videos

def get_correct_filenames(correct_videos):
    """Получить список правильных имен файлов"""
    
    correct_files = set()
    
    # Добавляем имена упражнений
    for video in correct_videos["exercises"]:
        filename = os.path.basename(video["target_path"])
        correct_files.add(filename)
    
    # Добавляем имена мотивационных
    for video in correct_videos["motivational"]:
        filename = os.path.basename(video["target_path"])
        correct_files.add(filename)
    
    print(f"📋 Всего правильных файлов: {len(correct_files)}")
    
    return correct_files

def cleanup_folder(folder_path, correct_files, folder_name):
    """Удалить лишние файлы из папки"""
    
    if not os.path.exists(folder_path):
        print(f"⚠️ Папка не существует: {folder_path}")
        return 0, 0
    
    all_files = []
    for file in os.listdir(folder_path):
        if file.endswith('.mp4'):
            all_files.append(file)
    
    files_to_delete = []
    files_to_keep = []
    
    for file in all_files:
        if file in correct_files:
            files_to_keep.append(file)
        else:
            files_to_delete.append(file)
    
    print(f"\n📁 Папка {folder_name}:")
    print(f"  Всего файлов: {len(all_files)}")
    print(f"  Оставить: {len(files_to_keep)}")
    print(f"  Удалить: {len(files_to_delete)}")
    
    # Удаляем лишние файлы
    deleted_count = 0
    for file in files_to_delete:
        try:
            file_path = os.path.join(folder_path, file)
            os.remove(file_path)
            deleted_count += 1
            if deleted_count % 50 == 0:
                print(f"    Удалено: {deleted_count}/{len(files_to_delete)}")
        except Exception as e:
            print(f"    ❌ Ошибка удаления {file}: {e}")
    
    return len(files_to_keep), deleted_count

def delete_unnecessary_folders():
    """Удалить ненужные папки полностью"""
    
    base_path = "/Volumes/Z9/AI_FITNESS_COACH_VIDEOS"
    
    # Папки, которые не должны существовать
    unnecessary_folders = ["instructions", "reminders"]
    
    deleted_folders = []
    
    for folder in unnecessary_folders:
        folder_path = os.path.join(base_path, folder)
        if os.path.exists(folder_path):
            # Подсчитываем файлы перед удалением
            file_count = len([f for f in os.listdir(folder_path) if f.endswith('.mp4')])
            
            # Удаляем все файлы в папке
            for file in os.listdir(folder_path):
                if file.endswith('.mp4'):
                    try:
                        os.remove(os.path.join(folder_path, file))
                    except:
                        pass
            
            # Удаляем саму папку
            try:
                os.rmdir(folder_path)
                deleted_folders.append(folder)
                print(f"🗑️ Удалена папка {folder} ({file_count} файлов)")
            except Exception as e:
                print(f"⚠️ Не удалось удалить папку {folder}: {e}")
    
    return deleted_folders

def generate_cleanup_report(before_counts, after_counts, correct_videos):
    """Создать отчет об очистке"""
    
    report = f"""# 🧹 ОТЧЕТ ОБ ОЧИСТКЕ ВИДЕО

## Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 РЕЗУЛЬТАТЫ ОЧИСТКИ:

### До очистки:
- exercises: {before_counts.get('exercises', 0)} файлов
- motivation: {before_counts.get('motivation', 0)} файлов  
- weekly: {before_counts.get('weekly', 0)} файлов
- progress: {before_counts.get('progress', 0)} файлов
- final: {before_counts.get('final', 0)} файлов
- instructions: {before_counts.get('instructions', 0)} файлов
- **ВСЕГО: {sum(before_counts.values())} файлов**

### После очистки:
- exercises: {after_counts.get('exercises', 0)} файлов (должно быть 271)
- motivation: {after_counts.get('motivation', 0)} файлов (должно быть 315)
- weekly: {after_counts.get('weekly', 0)} файлов (должно быть 18)
- progress: {after_counts.get('progress', 0)} файлов (должно быть 9)
- final: {after_counts.get('final', 0)} файлов (должно быть 3)
- **ВСЕГО: {sum(after_counts.values())} файлов (должно быть 616)**

### Удалено:
- exercises: {before_counts.get('exercises', 0) - after_counts.get('exercises', 0)} файлов
- motivation: {before_counts.get('motivation', 0) - after_counts.get('motivation', 0)} файлов
- weekly: {before_counts.get('weekly', 0) - after_counts.get('weekly', 0)} файлов
- progress: {before_counts.get('progress', 0) - after_counts.get('progress', 0)} файлов
- final: {before_counts.get('final', 0) - after_counts.get('final', 0)} файлов
- instructions: {before_counts.get('instructions', 0)} файлов (папка удалена)
- **ВСЕГО УДАЛЕНО: {sum(before_counts.values()) - sum(after_counts.values())} файлов**

## ✅ СТАТУС:

"""
    
    expected = {
        "exercises": 271,
        "motivation": 315,
        "weekly": 18,
        "progress": 9,
        "final": 3
    }
    
    all_correct = True
    for folder, expected_count in expected.items():
        actual_count = after_counts.get(folder, 0)
        if actual_count == expected_count:
            report += f"✅ {folder}: {actual_count} = {expected_count} (правильно)\n"
        else:
            report += f"❌ {folder}: {actual_count} ≠ {expected_count} (неправильно)\n"
            all_correct = False
    
    if all_correct and sum(after_counts.values()) == 616:
        report += "\n## 🎉 УСПЕХ! Система приведена к правильному состоянию: 616 видео"
    else:
        report += f"\n## ⚠️ ВНИМАНИЕ! Количество видео не соответствует плану"
        report += f"\nИмеется: {sum(after_counts.values())} видео"
        report += f"\nДолжно быть: 616 видео"
        report += f"\nРазница: {sum(after_counts.values()) - 616} видео"
    
    return report

def main():
    """Основная функция очистки"""
    
    print("🧹 ОЧИСТКА ДУБЛИКАТОВ И ЛИШНИХ ВИДЕО")
    print("=" * 50)
    
    base_path = "/Volumes/Z9/AI_FITNESS_COACH_VIDEOS"
    
    # 1. Загружаем списки правильных видео
    print("\n📋 Шаг 1: Загрузка списков правильных видео...")
    correct_videos = load_correct_video_lists()
    
    if not correct_videos:
        print("❌ Не удалось загрузить списки правильных видео!")
        return
    
    # 2. Получаем правильные имена файлов
    print("\n📝 Шаг 2: Формирование списка правильных файлов...")
    correct_files = get_correct_filenames(correct_videos)
    
    # Разделяем файлы по папкам
    correct_by_folder = {
        "exercises": set(),
        "motivation": set(),
        "weekly": set(),
        "progress": set(),
        "final": set()
    }
    
    for video in correct_videos["exercises"]:
        filename = os.path.basename(video["target_path"])
        correct_by_folder["exercises"].add(filename)
    
    for video in correct_videos["motivational"]:
        filename = os.path.basename(video["target_path"])
        folder = video["target_path"].split('/')[-2]  # Получаем имя папки
        if folder in correct_by_folder:
            correct_by_folder[folder].add(filename)
    
    # 3. Подсчитываем файлы ДО очистки
    print("\n📊 Шаг 3: Подсчет файлов до очистки...")
    before_counts = {}
    folders = ["exercises", "motivation", "weekly", "progress", "final", "instructions"]
    
    for folder in folders:
        folder_path = os.path.join(base_path, folder)
        if os.path.exists(folder_path):
            count = len([f for f in os.listdir(folder_path) if f.endswith('.mp4')])
            before_counts[folder] = count
            print(f"  {folder}: {count} файлов")
        else:
            before_counts[folder] = 0
    
    print(f"  ВСЕГО: {sum(before_counts.values())} файлов")
    
    # 4. Удаляем ненужные папки
    print("\n🗑️ Шаг 4: Удаление ненужных папок...")
    deleted_folders = delete_unnecessary_folders()
    
    # 5. Очищаем папки от дубликатов
    print("\n🧹 Шаг 5: Очистка папок от дубликатов...")
    after_counts = {}
    
    for folder, correct_files_for_folder in correct_by_folder.items():
        folder_path = os.path.join(base_path, folder)
        kept, deleted = cleanup_folder(folder_path, correct_files_for_folder, folder)
        after_counts[folder] = kept
        
        if deleted > 0:
            print(f"  ✅ {folder}: удалено {deleted} лишних файлов")
    
    # 6. Подсчитываем файлы ПОСЛЕ очистки
    print("\n📊 Шаг 6: Подсчет файлов после очистки...")
    for folder in ["exercises", "motivation", "weekly", "progress", "final"]:
        folder_path = os.path.join(base_path, folder)
        if os.path.exists(folder_path):
            count = len([f for f in os.listdir(folder_path) if f.endswith('.mp4')])
            after_counts[folder] = count
            print(f"  {folder}: {count} файлов")
    
    print(f"  ВСЕГО: {sum(after_counts.values())} файлов")
    
    # 7. Создаем отчет
    print("\n📄 Шаг 7: Создание отчета...")
    report = generate_cleanup_report(before_counts, after_counts, correct_videos)
    
    report_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/CLEANUP_REPORT.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Отчет сохранен: {report_file}")
    
    # Итог
    print("\n" + "=" * 50)
    print("🎉 ОЧИСТКА ЗАВЕРШЕНА!")
    print(f"📊 Было: {sum(before_counts.values())} файлов")
    print(f"📊 Стало: {sum(after_counts.values())} файлов")
    print(f"🗑️ Удалено: {sum(before_counts.values()) - sum(after_counts.values())} файлов")
    
    if sum(after_counts.values()) == 616:
        print("✅ УСПЕХ! Система содержит ровно 616 видео как и планировалось!")
    else:
        print(f"⚠️ ВНИМАНИЕ! В системе {sum(after_counts.values())} видео вместо 616")

if __name__ == '__main__':
    main()