#!/usr/bin/env python3
"""
Обновление AI промптов с ПОЛНЫМ списком всех exercise_slug
"""

import os
import csv

def get_all_exercise_slugs():
    """Получает ВСЕ exercise_slug из CSV файла"""
    csv_file = "/Users/alexbel/Desktop/AI Fitness Coach/media_lists/EXERCISES_271_VIDEOS.csv"
    
    slugs = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            slug = row['exercise_slug'].strip()
            if slug and slug not in slugs:
                slugs.append(slug)
    
    return sorted(slugs)

def format_exercise_list(slugs, max_per_line=10):
    """Форматирует список упражнений с переносами строк"""
    formatted_lines = []
    
    for i in range(0, len(slugs), max_per_line):
        chunk = slugs[i:i+max_per_line]
        formatted_lines.append(", ".join(chunk))
    
    return ",\n".join(formatted_lines)

def update_prompt_file_full(prompt_file, all_exercise_list):
    """Обновляет файл промпта с ПОЛНЫМ списком упражнений"""
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Найти и заменить строку с exercise_slug
    old_line_start = "ВАЖНО: Используй ТОЛЬКО эти exercise_slug'и:"
    
    # Найти начало старой строки
    start_idx = content.find(old_line_start)
    if start_idx == -1:
        print(f"  ⚠️ Не найдена строка с exercise_slug в {prompt_file}")
        return False
    
    # Найти конец (следующий абзац)
    next_paragraph_idx = content.find("\n\nСоздай план", start_idx)
    if next_paragraph_idx == -1:
        next_paragraph_idx = content.find("\n\n", start_idx + len(old_line_start))
        if next_paragraph_idx == -1:
            # Если не найден следующий абзац, ищем до конца файла
            next_paragraph_idx = len(content)
    
    # Создать новую секцию
    new_section = f"""{old_line_start}

{all_exercise_list}

КАТЕГОРИИ УПРАЖНЕНИЙ ДЛЯ СПРАВКИ:
- Разминка (warmup): упражнения со словами warmup, gentle, circles, rolls, swings
- Силовые (strength): push_ups, squats, pull_ups, lunges, rows, bridges
- Кардио (cardio): burpees, mountain_climbers, jumping, high_knees
- Кор (core): plank, crunches, bicycle, dead_bug, russian_twists
- Гибкость (flexibility): stretch, pose, hold, relax

ИНСТРУКЦИИ ПО ВЫБОРУ УПРАЖНЕНИЙ:
1. Выбирай 4-6 упражнений за тренировку
2. Комбинируй разные группы мышц  
3. Начинай с разминки (warmup упражнения)
4. Включай силовые упражнения как основу
5. Добавляй кардио для интенсивности
6. Заканчивай растяжкой (flexibility упражнения)
7. Учитывай уровень пользователя при выборе сложности"""
    
    # Заменить содержимое
    new_content = content[:start_idx] + new_section + content[next_paragraph_idx:]
    
    # Сохранить файл
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def main():
    print("🚀 ОБНОВЛЕНИЕ AI ПРОМПТОВ С ПОЛНЫМ СПИСКОМ УПРАЖНЕНИЙ")
    print("=" * 60)
    
    # Получить ВСЕ упражнения
    print("\n📋 Извлечение ВСЕХ exercise_slug из CSV...")
    all_slugs = get_all_exercise_slugs()
    print(f"  📊 Найдено {len(all_slugs)} уникальных exercise_slug")
    
    # Форматировать список
    print("\n📝 Форматирование полного списка...")
    formatted_list = format_exercise_list(all_slugs, max_per_line=8)
    
    # Показать превью
    preview_lines = formatted_list.split('\n')[:3]
    print(f"  📄 Превью (первые 3 строки):")
    for line in preview_lines:
        print(f"     {line}")
    print(f"     ... и еще {len(formatted_list.split()) - len(' '.join(preview_lines).split())} упражнений")
    
    # Список файлов для обновления
    prompt_files = [
        "/Users/alexbel/Desktop/AI Fitness Coach/prompts/workout_plan_bro.txt",
        "/Users/alexbel/Desktop/AI Fitness Coach/prompts/workout_plan_sergeant.txt", 
        "/Users/alexbel/Desktop/AI Fitness Coach/prompts/workout_plan_intellectual.txt"
    ]
    
    print(f"\n🔄 Обновление промпт файлов с ПОЛНЫМ списком...")
    
    for prompt_file in prompt_files:
        if os.path.exists(prompt_file):
            print(f"  📝 Обновление {os.path.basename(prompt_file)}...")
            success = update_prompt_file_full(prompt_file, formatted_list)
            if success:
                print(f"     ✅ Успешно обновлен с {len(all_slugs)} упражнениями")
            else:
                print(f"     ❌ Ошибка обновления")
        else:
            print(f"  ⚠️ Файл не найден: {prompt_file}")
    
    # Создать справочный файл по категориям
    categories_file = "/Users/alexbel/Desktop/AI Fitness Coach/EXERCISE_CATEGORIES.md"
    
    # Простая категоризация по ключевым словам
    categories = {
        'Разминка (Warmup)': [s for s in all_slugs if any(kw in s.lower() for kw in ['warmup', 'gentle', 'circles', 'rolls', 'swings', 'marching'])],
        'Силовые (Strength)': [s for s in all_slugs if any(kw in s.lower() for kw in ['push_ups', 'squats', 'pull_ups', 'lunges', 'rows', 'bridge'])],
        'Кардио (Cardio)': [s for s in all_slugs if any(kw in s.lower() for kw in ['burpees', 'mountain', 'jumping', 'knees', 'jacks'])],
        'Кор (Core)': [s for s in all_slugs if any(kw in s.lower() for kw in ['plank', 'crunches', 'bicycle', 'dead_bug', 'russian', 'abs'])],
        'Гибкость (Flexibility)': [s for s in all_slugs if any(kw in s.lower() for kw in ['stretch', 'pose', 'hold', 'relax', 'fold'])]
    }
    
    with open(categories_file, 'w', encoding='utf-8') as f:
        f.write("# 🏋️ СПРАВОЧНИК УПРАЖНЕНИЙ ДЛЯ AI\n\n")
        f.write(f"**Всего упражнений:** {len(all_slugs)}\n\n")
        
        for category, exercises in categories.items():
            f.write(f"## {category} ({len(exercises)} упражнений)\n\n")
            # Группируем по 6 в строке для читаемости
            for i in range(0, len(exercises), 6):
                chunk = exercises[i:i+6]
                f.write("- " + ", ".join(f"`{ex}`" for ex in chunk) + "\n")
            f.write("\n")
        
        # Все остальные упражнения
        categorized = set()
        for exercises in categories.values():
            categorized.update(exercises)
        
        other_exercises = [s for s in all_slugs if s not in categorized]
        if other_exercises:
            f.write(f"## Другие упражнения ({len(other_exercises)})\n\n")
            for i in range(0, len(other_exercises), 6):
                chunk = other_exercises[i:i+6]
                f.write("- " + ", ".join(f"`{ex}`" for ex in chunk) + "\n")
    
    print(f"\n📄 Создан справочник: EXERCISE_CATEGORIES.md")
    
    print("\n" + "=" * 60)
    print("✅ ПОЛНОЕ ОБНОВЛЕНИЕ ЗАВЕРШЕНО!")
    print(f"\n📊 Статистика:")
    print(f"   🎯 AI теперь имеет доступ к: {len(all_slugs)} упражнениям")
    print(f"   📁 Обновлено файлов: {len(prompt_files)}")
    print(f"   📋 Создан справочник по категориям")
    
    print(f"\n🎯 Преимущества:")
    print("   🎨 Максимальное разнообразие планов")
    print("   🎯 AI может создавать специализированные тренировки")
    print("   📈 Использование всей библиотеки видео")
    print("   🔄 Полная синхронизация AI ↔ Видео")

if __name__ == "__main__":
    main()