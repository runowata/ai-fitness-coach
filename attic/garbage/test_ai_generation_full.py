#!/usr/bin/env python
"""
Полная диагностика AI генерации планов тренировок
"""
import os
import sys
import django
import json
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/Users/alexbel/Desktop/Проекты/AI Fitness Coach')
django.setup()

from django.contrib.auth import get_user_model
from apps.onboarding.services import OnboardingDataProcessor
from apps.ai_integration.services import WorkoutPlanGenerator
from apps.workouts.models import WorkoutPlan
from django.conf import settings

User = get_user_model()

def main():
    print("=" * 70)
    print("🔍 ПОЛНАЯ ДИАГНОСТИКА AI СИСТЕМЫ")
    print("=" * 70)
    
    # 1. Проверка настроек
    print("\n📋 1. ПРОВЕРКА НАСТРОЕК:")
    print(f"   - OPENAI_MODEL: {settings.OPENAI_MODEL}")
    print(f"   - OPENAI_MODEL_MINI: {settings.OPENAI_MODEL_MINI}")
    api_key = settings.OPENAI_API_KEY
    if api_key:
        print(f"   - OPENAI_API_KEY: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '***'}")
    else:
        print("   - OPENAI_API_KEY: ❌ НЕ УСТАНОВЛЕН!")
        return
    
    # 2. Получение пользователя
    print("\n👤 2. ПРОВЕРКА ПОЛЬЗОВАТЕЛЯ:")
    try:
        user = User.objects.get(email='diagnostic@test.com')
        print(f"   ✅ Пользователь найден: {user.email}")
        print(f"   - Архетип: {user.profile.archetype}")
        print(f"   - Онбординг ответов: {user.onboarding_responses.count()}")
    except User.DoesNotExist:
        print("   ❌ Пользователь не найден!")
        return
    
    # 3. Обработка данных онбординга
    print("\n📊 3. ОБРАБОТКА ДАННЫХ ОНБОРДИНГА:")
    try:
        user_data = OnboardingDataProcessor.collect_user_data(user)
        print(f"   ✅ Собрано {len(user_data)} полей данных")
        print(f"   - Возраст: {user_data.get('age', 'N/A')}")
        print(f"   - Рост: {user_data.get('height', 'N/A')} см")
        print(f"   - Вес: {user_data.get('weight', 'N/A')} кг")
        print(f"   - Цель: {user_data.get('primary_goal', 'N/A')}")
        print(f"   - Архетип: {user_data.get('archetype', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Ошибка обработки данных: {e}")
        return
    
    # 4. Генерация AI плана
    print("\n🤖 4. ГЕНЕРАЦИЯ AI ПЛАНА:")
    print("   Запуск генерации...")
    
    start_time = time.time()
    generator = WorkoutPlanGenerator()
    
    try:
        # Пытаемся сгенерировать план
        result = generator.generate_plan(
            user_data=user_data,
            use_comprehensive=True
        )
        
        generation_time = time.time() - start_time
        
        print(f"\n   ✅ План сгенерирован за {generation_time:.1f} секунд")
        
        # 5. Анализ результата
        print("\n📈 5. АНАЛИЗ РЕЗУЛЬТАТА:")
        
        # Проверяем, использовался ли fallback
        if result.get('fallback_used'):
            print("   ⚠️ ИСПОЛЬЗОВАН FALLBACK (не реальный AI)")
            print(f"   - Причина: {result.get('fallback_reason', 'Неизвестно')}")
        else:
            print("   ✅ Использован реальный AI")
        
        # Проверяем наличие comprehensive анализа
        if result.get('comprehensive'):
            print("   ✅ Comprehensive анализ выполнен")
            if 'analysis' in result:
                print("   - Анализ пользователя присутствует")
                print("   - Система мотивации присутствует")
                print("   - Долгосрочная стратегия присутствует")
        else:
            print("   ⚠️ Comprehensive анализ НЕ выполнен")
        
        # Анализ плана тренировок
        training_program = result.get('training_program', {})
        if training_program:
            weeks = training_program.get('weeks', [])
            print(f"\n   📅 СТРУКТУРА ПЛАНА:")
            print(f"   - Недель в плане: {len(weeks)}")
            
            total_workouts = 0
            total_exercises = 0
            
            for week in weeks:
                days = week.get('days', [])
                total_workouts += len(days)
                for day in days:
                    exercises = day.get('exercises', [])
                    total_exercises += len(exercises)
            
            print(f"   - Всего тренировок: {total_workouts}")
            print(f"   - Всего упражнений: {total_exercises}")
            
            # Примеры упражнений
            if weeks and weeks[0].get('days'):
                first_day = weeks[0]['days'][0]
                print(f"\n   💪 ПРИМЕР ТРЕНИРОВКИ (Неделя 1, День 1):")
                for i, ex in enumerate(first_day.get('exercises', [])[:3], 1):
                    print(f"      {i}. {ex.get('exercise_slug', 'Unknown')}: {ex.get('sets', 0)}x{ex.get('reps', 0)}")
        
        # 6. Сохранение в базу данных
        print("\n💾 6. СОХРАНЕНИЕ В БАЗУ ДАННЫХ:")
        try:
            # Удаляем старые планы
            WorkoutPlan.objects.filter(user=user).delete()
            
            # Создаем новый план
            plan = WorkoutPlan.objects.create(
                user=user,
                name=result.get('goal', 'Персональный план'),
                duration_weeks=len(training_program.get('weeks', [])),
                goal=result.get('goal', 'Общая физическая подготовка'),
                plan_data=json.dumps(training_program),
                description=result.get('description', ''),
                motivation_text=result.get('motivation_text', ''),
                user_analysis=result.get('analysis', {}),
                long_term_strategy=result.get('long_term_strategy', {}),
                is_active=True
            )
            print(f"   ✅ План сохранен в БД с ID: {plan.id}")
        except Exception as e:
            print(f"   ❌ Ошибка сохранения: {e}")
        
    except Exception as e:
        print(f"\n   ❌ ОШИБКА ГЕНЕРАЦИИ: {e}")
        import traceback
        print("\n   ДЕТАЛИ ОШИБКИ:")
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("=" * 70)

if __name__ == '__main__':
    main()