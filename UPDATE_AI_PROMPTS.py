#!/usr/bin/env python3
"""
Обновление AI промптов с актуальными exercise_slug из загруженных видео
"""

import os
import csv

def get_exercise_slugs_from_csv():
    """Получает все exercise_slug из CSV файла"""
    csv_file = "/Users/alexbel/Desktop/AI Fitness Coach/media_lists/EXERCISES_271_VIDEOS.csv"
    
    slugs = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            slug = row['exercise_slug'].strip()
            if slug and slug not in slugs:
                slugs.append(slug)
    
    return sorted(slugs)

def categorize_exercises(slugs):
    """Категоризирует упражнения по типам"""
    categories = {
        'warmup': [],
        'main_strength': [],
        'cardio': [],
        'core': [],
        'flexibility': []
    }
    
    # Ключевые слова для категоризации
    warmup_keywords = ['warmup', 'gentle', 'light', 'marching', 'circles', 'rolls', 'swings']
    cardio_keywords = ['jumping', 'burpees', 'mountain', 'high_knees', 'butt_kicks', 'jacks']
    core_keywords = ['plank', 'abs', 'crunches', 'bicycle', 'russian', 'dead_bug', 'bird_dog']
    strength_keywords = ['push_ups', 'squats', 'lunges', 'pull_ups', 'deadlifts', 'rows']
    flexibility_keywords = ['stretch', 'pose', 'hold', 'release']
    
    for slug in slugs:
        slug_lower = slug.lower()
        
        if any(kw in slug_lower for kw in warmup_keywords):
            categories['warmup'].append(slug)
        elif any(kw in slug_lower for kw in core_keywords):
            categories['core'].append(slug)
        elif any(kw in slug_lower for kw in cardio_keywords):
            categories['cardio'].append(slug)
        elif any(kw in slug_lower for kw in strength_keywords):
            categories['main_strength'].append(slug)
        elif any(kw in slug_lower for kw in flexibility_keywords):
            categories['flexibility'].append(slug)
        else:
            # По умолчанию - основные упражнения
            categories['main_strength'].append(slug)
    
    return categories

def update_prompt_file(prompt_file, new_exercise_list):
    """Обновляет файл промпта с новым списком упражнений"""
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Найти и заменить строку с exercise_slug
    old_line_start = "ВАЖНО: Используй ТОЛЬКО эти exercise_slug'и:"
    old_line_end = "deadlifts, pull-ups"
    
    # Найти начало и конец старой строки
    start_idx = content.find(old_line_start)
    if start_idx == -1:
        print(f"  ⚠️ Не найдена строка с exercise_slug в {prompt_file}")
        return False
    
    end_idx = content.find(old_line_end, start_idx)
    if end_idx == -1:
        print(f"  ⚠️ Не найден конец строки в {prompt_file}")
        return False
    
    end_idx += len(old_line_end)
    
    # Создать новую строку
    new_line = f"{old_line_start}\n{new_exercise_list}"
    
    # Заменить содержимое
    new_content = content[:start_idx] + new_line + content[end_idx:]
    
    # Сохранить файл
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def main():
    print("🔄 ОБНОВЛЕНИЕ AI ПРОМПТОВ С АКТУАЛЬНЫМИ EXERCISE_SLUG")
    print("=" * 55)
    
    # Получить список упражнений
    print("\n📋 Извлечение exercise_slug из CSV...")
    slugs = get_exercise_slugs_from_csv()
    print(f"  📊 Найдено {len(slugs)} уникальных exercise_slug")
    
    # Категоризировать упражнения
    print("\n🏷️ Категоризация упражнений...")
    categories = categorize_exercises(slugs)
    
    for category, exercises in categories.items():
        print(f"  {category}: {len(exercises)} упражнений")
    
    # Создать списки для разных случаев
    # Топ 30 самых популярных упражнений для основных промптов
    popular_exercises = (
        # Основные силовые
        categories['main_strength'][:15] +
        # Кардио
        categories['cardio'][:8] +
        # Кор
        categories['core'][:5] +
        # Разминка
        categories['warmup'][:2]
    )[:30]
    
    # Полный список для расширенных промптов
    all_exercises = slugs
    
    # Форматировать списки
    popular_list = ", ".join(popular_exercises)
    
    # Для больших списков - разбить по строкам
    all_list_formatted = ""
    chunk_size = 8
    for i in range(0, len(all_exercises), chunk_size):
        chunk = all_exercises[i:i+chunk_size]
        all_list_formatted += ", ".join(chunk)
        if i + chunk_size < len(all_exercises):
            all_list_formatted += ",\n"
    
    print(f"\n📝 Создание обновленных списков...")
    print(f"  🎯 Популярные (30): {len(popular_exercises)} упражнений")
    print(f"  📚 Полный список: {len(all_exercises)} упражнений")
    
    # Список файлов для обновления
    prompt_files = [
        "/Users/alexbel/Desktop/AI Fitness Coach/prompts/workout_plan_bro.txt",
        "/Users/alexbel/Desktop/AI Fitness Coach/prompts/workout_plan_sergeant.txt", 
        "/Users/alexbel/Desktop/AI Fitness Coach/prompts/workout_plan_intellectual.txt"
    ]
    
    print(f"\n🔄 Обновление промпт файлов...")
    
    for prompt_file in prompt_files:
        if os.path.exists(prompt_file):
            print(f"  📝 Обновление {os.path.basename(prompt_file)}...")
            success = update_prompt_file(prompt_file, popular_list)
            if success:
                print(f"     ✅ Успешно обновлен")
            else:
                print(f"     ❌ Ошибка обновления")
        else:
            print(f"  ⚠️ Файл не найден: {prompt_file}")
    
    # Создать файл с полным списком для справки
    full_list_file = "/Users/alexbel/Desktop/AI Fitness Coach/FULL_EXERCISE_SLUGS.txt"
    with open(full_list_file, 'w', encoding='utf-8') as f:
        f.write("# ПОЛНЫЙ СПИСОК EXERCISE_SLUG ДЛЯ AI ПРОМПТОВ\n")
        f.write(f"# Всего упражнений: {len(all_exercises)}\n")
        f.write(f"# Сгенерировано автоматически из EXERCISES_271_VIDEOS.csv\n\n")
        
        f.write("## ПОПУЛЯРНЫЕ УПРАЖНЕНИЯ (ДЛЯ ОСНОВНЫХ ПРОМПТОВ):\n")
        f.write(popular_list + "\n\n")
        
        f.write("## ВСЕ УПРАЖНЕНИЯ ПО КАТЕГОРИЯМ:\n\n")
        for category, exercises in categories.items():
            f.write(f"### {category.upper()}:\n")
            f.write(", ".join(exercises) + "\n\n")
        
        f.write("## ВСЕ УПРАЖНЕНИЯ (АЛФАВИТНЫЙ ПОРЯДОК):\n")
        f.write(all_list_formatted)
    
    print(f"\n📄 Создан справочный файл: FULL_EXERCISE_SLUGS.txt")
    
    print("\n" + "=" * 55)
    print("✅ ОБНОВЛЕНИЕ ПРОМПТОВ ЗАВЕРШЕНО!")
    print(f"\n📊 Статистика:")
    print(f"   🎯 В промптах теперь: {len(popular_exercises)} популярных упражнений")
    print(f"   📚 Всего доступно: {len(all_exercises)} упражнений")
    print(f"   📁 Обновлено файлов: {len(prompt_files)}")
    
    print(f"\n🎯 Следующие шаги:")
    print("1. Проверьте обновленные промпт файлы")
    print("2. Протестируйте AI генерацию планов")
    print("3. Убедитесь что AI использует новые exercise_slug")

if __name__ == "__main__":
    main()