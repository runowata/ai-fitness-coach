#!/usr/bin/env python3
"""
Симуляция полного процесса онбординга пользователя 
и генерация итогового промпта для GPT-5
"""

import json
import os
from pathlib import Path

# Симулируем ответы типичного пользователя
def create_simulated_user_data():
    """Создаем данные пользователя, который прошел полный онбординг"""
    
    # Базовые данные пользователя
    user_profile = {
        'age': 28,
        'height': 178,
        'weight': 82,
        'biological_sex': 'male',
        'fitness_level': 'intermediate',
        'primary_goal': 'muscle_gain',
        'archetype': 'mentor',  # Выбрал "Мудрого наставника"
        
        # Травмы и ограничения
        'injuries': 'lower_back_issues',
        'medical_conditions': 'none',
        
        # Оборудование и логистика
        'equipment_list': ['dumbbells', 'resistance_bands', 'pull_up_bar'],
        'workout_frequency': 4,  # 4 раза в неделю
        'workout_duration': 60,  # 60 минут
        'duration_weeks': 6,     # 6-недельный план
        
        # Предпочтения
        'preferred_workout_time': 'evening',
        'training_experience': 'intermediate',
        'motivation_level': 'high',
    }
    
    # Детальные ответы онбординга (как будто из базы данных)
    detailed_onboarding = {
        # Блок 1: Физические параметры
        'current_fitness_assessment': 'can_do_20_pushups',
        'energy_levels': 'moderate_energy',
        'sleep_quality': 'good_7_8_hours',
        'stress_levels': 'moderate_work_stress',
        
        # Блок 2: Цели и мотивация  
        'specific_goals': ['build_muscle_mass', 'increase_strength', 'improve_posture'],
        'motivation_sources': ['personal_achievement', 'health_benefits', 'confidence_boost'],
        'success_definition': 'visible_muscle_growth_in_6_weeks',
        'past_workout_experience': 'gym_experience_2_years_ago',
        
        # Блок 3: Ограничения и препятствия
        'time_constraints': 'busy_work_schedule_but_committed',
        'physical_limitations': 'occasional_lower_back_pain_from_desk_work', 
        'mental_barriers': 'fear_of_not_seeing_results_quickly',
        'previous_failures': 'stopped_gym_after_3_months_lack_of_progress',
        
        # Блок 4: Предпочтения и контекст
        'workout_environment': 'home_with_some_equipment',
        'music_preferences': 'upbeat_electronic_music',
        'social_aspect': 'prefer_solo_workouts',
        'learning_style': 'visual_learner_needs_demonstrations',
        
        # Блок 5: Специфичные детали
        'body_focus_areas': ['chest', 'shoulders', 'arms', 'core'],
        'cardio_preferences': 'minimal_cardio_focus_on_strength',
        'flexibility_interest': 'moderate_for_back_health',
        'nutrition_readiness': 'willing_to_make_moderate_changes',
        
        # Дополнительная мотивационная информация
        'personal_why': 'want_to_feel_confident_and_strong_again',
        'support_system': 'supportive_partner_encouraging',
        'accountability_preference': 'self_directed_with_guidance',
        'reward_motivation': 'internal_satisfaction_and_progress_photos'
    }
    
    return user_profile, detailed_onboarding

def load_system_prompt(archetype='mentor'):
    """Загружает системный промпт для выбранного архетипа"""
    prompts_dir = Path('/Users/alexbel/Desktop/Проекты/AI Fitness Coach/prompts/v2')
    system_file = prompts_dir / 'system' / f'master_{archetype}.system.md'
    
    if system_file.exists():
        return system_file.read_text(encoding='utf-8')
    else:
        return f"# Архетип: {archetype}\nВы профессиональный фитнес тренер."

def load_user_prompt_template(archetype='mentor'):
    """Загружает пользовательский промпт-шаблон"""
    prompts_dir = Path('/Users/alexbel/Desktop/Проекты/AI Fitness Coach/prompts/v2')
    user_file = prompts_dir / 'user' / f'master_{archetype}.user.md'
    
    if user_file.exists():
        return user_file.read_text(encoding='utf-8')
    else:
        return "Создайте план тренировок для пользователя с данными: {{onboarding_payload_json}}"

def format_equipment_list(equipment_list):
    """Форматирует список оборудования"""
    equipment_mapping = {
        'dumbbells': 'Гантели',
        'resistance_bands': 'Эластичные ленты', 
        'pull_up_bar': 'Турник',
        'kettlebell': 'Гиря',
        'barbell': 'Штанга'
    }
    
    formatted = [equipment_mapping.get(eq, eq) for eq in equipment_list]
    return ', '.join(formatted)

def generate_final_prompt():
    """Генерирует финальный промпт который отправляется в GPT-5"""
    
    # Получаем данные пользователя
    user_profile, detailed_onboarding = create_simulated_user_data()
    archetype = user_profile['archetype']
    
    # Загружаем промпты
    system_prompt = load_system_prompt(archetype)
    user_template = load_user_prompt_template(archetype)
    
    # Подготавливаем данные для подстановки
    template_vars = {
        'age': user_profile['age'],
        'height': user_profile['height'],
        'weight': user_profile['weight'],
        'primary_goal': user_profile['primary_goal'],
        'injuries': user_profile['injuries'],
        'equipment_list': format_equipment_list(user_profile['equipment_list']),
        'duration_weeks': user_profile['duration_weeks'],
        'onboarding_payload_json': json.dumps(detailed_onboarding, indent=2, ensure_ascii=False)
    }
    
    # Заполняем шаблон
    user_prompt = user_template
    for key, value in template_vars.items():
        user_prompt = user_prompt.replace(f'{{{{{key}}}}}', str(value))
    
    return system_prompt, user_prompt, user_profile, detailed_onboarding

def main():
    """Основная функция для демонстрации полного промпта"""
    
    print("🧠 СИМУЛЯЦИЯ ПОЛНОГО ОНБОРДИНГА ПОЛЬЗОВАТЕЛЯ")
    print("=" * 60)
    
    # Генерируем промпт
    system_prompt, user_prompt, user_profile, detailed_onboarding = generate_final_prompt()
    
    print("\n👤 ПРОФИЛЬ СИМУЛИРОВАННОГО ПОЛЬЗОВАТЕЛЯ:")
    print("-" * 40)
    print(f"Возраст: {user_profile['age']} лет")
    print(f"Физические параметры: {user_profile['height']} см, {user_profile['weight']} кг")
    print(f"Уровень: {user_profile['fitness_level']}")
    print(f"Цель: {user_profile['primary_goal']}")
    print(f"Архетип: {user_profile['archetype']}")
    print(f"Ограничения: {user_profile['injuries']}")
    print(f"Оборудование: {', '.join(user_profile['equipment_list'])}")
    print(f"План: {user_profile['duration_weeks']} недель, {user_profile['workout_frequency']} раз/неделю")
    
    print("\n🔍 ДЕТАЛЬНЫЕ ОТВЕТЫ ОНБОРДИНГА:")
    print("-" * 40)
    for key, value in detailed_onboarding.items():
        if isinstance(value, list):
            value = ', '.join(value)
        print(f"{key}: {value}")
    
    print("\n" + "=" * 80)
    print("🤖 ФИНАЛЬНЫЙ ПРОМПТ ДЛЯ GPT-5")
    print("=" * 80)
    
    print("\n🔧 СИСТЕМНЫЙ ПРОМПТ (ROLE):")
    print("-" * 40)
    print(system_prompt)
    
    print("\n" + "-" * 80)
    print("📝 ПОЛЬЗОВАТЕЛЬСКИЙ ПРОМПТ (ЗАДАЧА):")
    print("-" * 80)
    print(user_prompt)
    
    print("\n" + "=" * 80)
    print("📊 ИТОГОВАЯ СТАТИСТИКА:")
    print("=" * 80)
    print(f"Длина системного промпта: {len(system_prompt)} символов")
    print(f"Длина пользовательского промпта: {len(user_prompt)} символов") 
    print(f"Общая длина: {len(system_prompt) + len(user_prompt)} символов")
    print(f"Количество детальных ответов: {len(detailed_onboarding)}")
    
    # Сохраняем в файл для анализа
    output_file = Path('/Users/alexbel/Desktop/Проекты/AI Fitness Coach/simulated_prompt_output.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("СИСТЕМНЫЙ ПРОМПТ:\n")
        f.write(system_prompt)
        f.write("\n\nПОЛЬЗОВАТЕЛЬСКИЙ ПРОМПТ:\n")
        f.write(user_prompt)
    
    print(f"\n💾 Полный промпт сохранен в: {output_file}")

if __name__ == "__main__":
    main()