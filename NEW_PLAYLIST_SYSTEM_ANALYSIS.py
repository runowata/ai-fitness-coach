#!/usr/bin/env python3
"""
Анализ новой системы генерации плейлистов
Основано на 616 видео и схеме: 3 недели все упражнения → обратная связь → 3 недели только 4-5 звезд
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.workouts.models import VideoClip, Exercise, WorkoutPlan, DailyWorkout

def analyze_current_ai_logic():
    """Анализ текущей логики AI генерации"""
    print("🔍 АНАЛИЗ ТЕКУЩЕЙ AI ЛОГИКИ ГЕНЕРАЦИИ ПЛЕЙЛИСТОВ")
    print("=" * 70)
    
    # Ищем файлы с AI промптами
    prompt_files = [
        '/Users/alexbel/Desktop/AI Fitness Coach/prompts/workout_plan_bro.txt',
        '/Users/alexbel/Desktop/AI Fitness Coach/prompts/workout_plan_sergeant.txt', 
        '/Users/alexbel/Desktop/AI Fitness Coach/prompts/workout_plan_intellectual.txt'
    ]
    
    print("\n📄 AI промпт файлы:")
    for file_path in prompt_files:
        if os.path.exists(file_path):
            print(f"  ✅ {os.path.basename(file_path)}")
            # Читаем первые строки для понимания структуры
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:10]
                print(f"     Первые строки: {len(lines)} строк")
        else:
            print(f"  ❌ {os.path.basename(file_path)} - не найден")
    
    # Анализируем текущие планы тренировок
    print(f"\n📊 Текущие планы в БД:")
    plans_count = WorkoutPlan.objects.count()
    active_plans = WorkoutPlan.objects.filter(is_active=True).count()
    
    print(f"  Всего планов: {plans_count}")
    print(f"  Активных планов: {active_plans}")
    
    if active_plans > 0:
        sample_plan = WorkoutPlan.objects.filter(is_active=True).first()
        print(f"\n🔍 Пример плана (ID: {sample_plan.id}):")
        print(f"  Название: {sample_plan.name}")
        print(f"  Недель: {sample_plan.duration_weeks}")
        print(f"  Цель: {sample_plan.goal}")
        
        # Анализируем структуру plan_data
        if sample_plan.plan_data:
            print(f"  Ключи в plan_data: {list(sample_plan.plan_data.keys())}")

def design_new_playlist_structure():
    """Проектирование новой структуры плейлистов"""
    print("\n\n🎯 НОВАЯ СТРУКТУРА ПЛЕЙЛИСТОВ НА ОСНОВЕ 616 ВИДЕО")
    print("=" * 70)
    
    # Структура наших реальных видео
    video_structure = {
        'exercises': {
            'warmup': {'count': 42, 'description': 'Разминочные упражнения'},
            'main': {'count': 145, 'description': 'Основные упражнения (105 базовых + 40 дополнительных)'},
            'endurance': {'count': 42, 'description': 'Сексуальная выносливость'}, 
            'cooldown': {'count': 42, 'description': 'Расслабление и растяжка'}
        },
        'motivational': {
            'intro': {'count': 63, 'description': 'Вступление и приветствие (21 день × 3 тренера)'},
            'after_warmup': {'count': 63, 'description': 'Мотивация после разминки'},
            'after_main': {'count': 63, 'description': 'Мотивация после основных'},
            'motivating_speech': {'count': 63, 'description': 'Мотивирующий ролик тренера'},
            'farewell': {'count': 63, 'description': 'Напутственное слово'},
            'weekly': {'count': 18, 'description': 'Еженедельные (6 недель × 3 тренера)'},
            'biweekly': {'count': 9, 'description': 'Двухнедельные (3 раза × 3 тренера)'},
            'final': {'count': 3, 'description': 'Финальные (3 тренера)'}
        }
    }
    
    print("\n📊 Структура видео для плейлистов:")
    
    for category, subcats in video_structure.items():
        print(f"\n🎬 {category.upper()}:")
        total = 0
        for subcat, info in subcats.items():
            print(f"  - {subcat:15}: {info['count']:3d} видео | {info['description']}")
            total += info['count']
        print(f"  📈 Итого {category}: {total} видео")
    
    # Логика распределения по неделям
    print(f"\n📅 ЛОГИКА РАСПРЕДЕЛЕНИЯ ПО 6 НЕДЕЛЯМ:")
    
    weeks_structure = {
        'week_1-3': {
            'name': 'Первые 3 недели',
            'strategy': 'Все упражнения без повторов',
            'daily_exercises': {
                'warmup': 2,      # 2 разминочных
                'main': 5,        # 5 основных
                'endurance': 2,   # 2 на выносливость
                'cooldown': 2     # 2 расслабляющих
            },
            'total_per_day': 11,
            'total_per_3_weeks': 11 * 21  # 231 упражнение за 3 недели
        },
        'feedback_collection': {
            'name': 'Сбор обратной связи',
            'strategy': 'Пользователь оценивает каждое упражнение от 1 до 5',
            'purpose': 'Определить любимые упражнения пользователя'
        },
        'week_4-6': {
            'name': 'Последние 3 недели', 
            'strategy': 'Только упражнения с оценками 4-5',
            'daily_exercises': {
                'warmup': 2,      # Только любимые разминочные
                'main': 5,        # Только любимые основные
                'endurance': 2,   # Только любимые на выносливость
                'cooldown': 2     # Только любимые расслабляющие
            },
            'total_per_day': 11,
            'selection_criteria': 'Рейтинг ≥ 4 звезды'
        }
    }
    
    for period, info in weeks_structure.items():
        print(f"\n📋 {info['name']}:")
        print(f"  🎯 Стратегия: {info['strategy']}")
        if 'daily_exercises' in info:
            print(f"  📊 Упражнений в день:")
            total_daily = 0
            for ex_type, count in info['daily_exercises'].items():
                print(f"    - {ex_type:10}: {count} видео")
                total_daily += count
            print(f"    📈 Итого: {total_daily} упражнений в день")
        if 'purpose' in info:
            print(f"  🎯 Цель: {info['purpose']}")
        if 'selection_criteria' in info:
            print(f"  ⭐ Критерий отбора: {info['selection_criteria']}")

def design_ai_prompt_structure():
    """Проектирование структуры AI промптов"""
    print(f"\n\n🤖 НОВАЯ СТРУКТУРА AI ПРОМПТОВ")
    print("=" * 70)
    
    prompt_structure = {
        'input_data': [
            'Архетип тренера (bro/sergeant/intellectual)',
            'Неделя курса (1-6)',
            'День недели (1-7)',
            'Доступные упражнения (полный список или отфильтрованный)',
            'История оценок пользователя (для недель 4-6)'
        ],
        'output_format': {
            'daily_structure': [
                {'type': 'motivational', 'category': 'intro', 'trainer_dependent': True},
                {'type': 'exercise', 'category': 'warmup', 'count': 2},
                {'type': 'motivational', 'category': 'after_warmup', 'trainer_dependent': True},
                {'type': 'exercise', 'category': 'main', 'count': 5},
                {'type': 'motivational', 'category': 'after_main', 'trainer_dependent': True},
                {'type': 'exercise', 'category': 'endurance', 'count': 2},
                {'type': 'motivational', 'category': 'motivating_speech', 'trainer_dependent': True},
                {'type': 'exercise', 'category': 'cooldown', 'count': 2},
                {'type': 'motivational', 'category': 'farewell', 'trainer_dependent': True}
            ],
            'special_days': {
                'sunday': 'weekly motivational video (10 min)',
                'every_2_weeks': 'biweekly progress video (15 min)',
                'final_day': 'final congratulation video'
            }
        },
        'constraints': [
            'Не повторять упражнения в первые 3 недели',
            'Использовать только 4-5 звездочные упражнения в последние 3 недели',
            'Мотивационные видео должны соответствовать дню курса и архетипу',
            'Соблюдать баланс групп мышц в основных упражнениях'
        ]
    }
    
    print(f"\n📥 Входные данные для AI:")
    for i, item in enumerate(prompt_structure['input_data'], 1):
        print(f"  {i}. {item}")
    
    print(f"\n📤 Формат выходных данных:")
    print(f"  🏗️ Структура дня ({len(prompt_structure['output_format']['daily_structure'])} элементов):")
    
    for i, item in enumerate(prompt_structure['output_format']['daily_structure'], 1):
        trainer_mark = " (👨‍🏫 от тренера)" if item.get('trainer_dependent') else ""
        count_mark = f" × {item['count']}" if 'count' in item else ""
        print(f"    {i:2d}. {item['type']:12} | {item['category']:15}{count_mark}{trainer_mark}")
    
    print(f"\n🎯 Ограничения и правила:")
    for i, constraint in enumerate(prompt_structure['constraints'], 1):
        print(f"  {i}. {constraint}")

def main():
    """Основная функция анализа"""
    print("🚀 АНАЛИЗ НОВОЙ СИСТЕМЫ ГЕНЕРАЦИИ ПЛЕЙЛИСТОВ")
    print("=" * 80)
    
    try:
        # Анализируем текущую логику
        analyze_current_ai_logic()
        
        # Проектируем новую структуру
        design_new_playlist_structure()
        
        # Проектируем AI промпты
        design_ai_prompt_structure()
        
        print(f"\n\n✅ АНАЛИЗ ЗАВЕРШЕН!")
        print("Определена структура новой системы генерации плейлистов на основе 616 видео.")
        print("Следующий шаг: реализация логики первых 3 недель и системы обратной связи.")
        
    except Exception as e:
        print(f"\n❌ Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()