#!/usr/bin/env python3
"""
Демонстрация ПОЛНОГО ПРОМПТА для GPT-5
Показывает реальные данные пользователя и промпт, который отправляется в API
"""

import os
import sys
import django

# Setup Django
sys.path.append('/Users/alexbel/Desktop/Проекты/AI Fitness Coach')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.ai_integration.workout_generator_gpt5 import create_gpt5_generator
from apps.core.services.exercise_validation import ExerciseValidationService
import json

def show_full_prompt():
    """Показать полный промпт для GPT-5"""
    
    # Создаем генератор
    generator = create_gpt5_generator()
    
    # РЕАЛЬНЫЕ ДАННЫЕ ПОЛЬЗОВАТЕЛЯ
    user_data = {
        'age': 32,
        'height': 175,
        'weight': 78,
        'archetype': 'mentor',  # Science-Based Coach
        'primary_goal': 'Снижение стресса и улучшение физической формы после долгой работы за компьютером',
        'injuries': 'Периодические боли в нижней части спины, напряжение в плечах и шее',
        'equipment_list': 'Домашний спортзал: гантели 5-30кг, фитбол, эластичные ленты, коврик для йоги, турник',
        'duration_weeks': 4,
        'onboarding_payload_json': json.dumps({
            'fitness_level': 'beginner',
            'work_stress_level': 'very_high', 
            'sleep_quality': 'poor',
            'training_frequency': 4,
            'preferred_workout_time': 'evening',
            'specific_concerns': ['lower_back_pain', 'stress_management', 'energy_levels', 'posture_correction'],
            'motivation_level': 'medium',
            'experience_years': 0.5,
            'current_activity': 'sedentary',
            'work_hours_per_day': 10,
            'screen_time_hours': 12,
            'lifestyle_factors': ['long_work_hours', 'irregular_schedule', 'high_stress_job', 'poor_posture']
        }, ensure_ascii=False, indent=2)
    }
    
    print("🔥 РЕАЛЬНЫЕ ДАННЫЕ ПОЛЬЗОВАТЕЛЯ")
    print("="*50)
    print(f"Возраст: {user_data['age']} лет")
    print(f"Рост/Вес: {user_data['height']}см, {user_data['weight']}кг")
    print(f"Архетип тренера: {user_data['archetype']} (Science-Based Coach)")
    print(f"Основная цель: {user_data['primary_goal']}")
    print(f"Травмы/ограничения: {user_data['injuries']}")
    print(f"Доступное оборудование: {user_data['equipment_list']}")
    print(f"Длительность программы: {user_data['duration_weeks']} недель")
    
    print("\n📋 ДЕТАЛЬНАЯ АНКЕТА ОНБОРДИНГА:")
    print(user_data['onboarding_payload_json'])
    
    # Получаем список упражнений для архетипа
    allowed_exercises = ExerciseValidationService.get_allowed_exercise_slugs(archetype='mentor')
    
    # Строим полные промпты
    system_prompt = generator._build_system_prompt('mentor')
    user_prompt = generator._build_user_prompt('mentor', user_data, allowed_exercises)
    
    print("\n" + "="*80)
    print("📤 ПОЛНЫЙ SYSTEM PROMPT ДЛЯ GPT-5:")
    print("="*80)
    print(system_prompt)
    
    print("\n" + "="*80)
    print("📤 ПОЛНЫЙ USER PROMPT ДЛЯ GPT-5:")
    print("="*80)
    print(user_prompt)
    
    print("\n" + "="*80)
    print("📊 СТАТИСТИКА ПРОМПТА:")
    print("="*80)
    print(f"System prompt длина: {len(system_prompt):,} символов")
    print(f"User prompt длина: {len(user_prompt):,} символов")
    print(f"ОБЩАЯ ДЛИНА: {len(system_prompt) + len(user_prompt):,} символов")
    print(f"Упражнений в whitelist: {len(allowed_exercises)} кодов")
    
    print(f"\n🎯 СПИСОК УПРАЖНЕНИЙ (первые 20 из {len(allowed_exercises)}):")
    sorted_exercises = sorted(allowed_exercises)
    for i, exercise in enumerate(sorted_exercises[:20]):
        print(f"  {exercise}")
    if len(sorted_exercises) > 20:
        print(f"  ... и еще {len(sorted_exercises) - 20} упражнений")
        
    print("\n" + "="*80)
    print("🚀 ЭТО РЕАЛЬНЫЙ ПРОМПТ, КОТОРЫЙ ОТПРАВЛЯЕТСЯ В GPT-5!")
    print("="*80)

if __name__ == "__main__":
    show_full_prompt()