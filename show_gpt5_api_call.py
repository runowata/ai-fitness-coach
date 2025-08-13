#!/usr/bin/env python3
"""
Демонстрация того, как симулированный промпт отправляется в GPT-5 через Responses API
"""

import json
from pathlib import Path


def show_gpt5_api_structure():
    """Показывает структуру API вызова к GPT-5"""
    
    # Загружаем созданный промпт
    prompt_file = Path('/Users/alexbel/Desktop/Проекты/AI Fitness Coach/simulated_prompt_output.txt')
    
    if not prompt_file.exists():
        print("❌ Сначала запустите simulate_user_onboarding.py")
        return
    
    content = prompt_file.read_text(encoding='utf-8')
    parts = content.split('\n\nПОЛЬЗОВАТЕЛЬСКИЙ ПРОМПТ:\n')
    
    system_prompt = parts[0].replace('СИСТЕМНЫЙ ПРОМПТ:\n', '')
    user_prompt = parts[1] if len(parts) > 1 else ""
    
    # JSON Schema для Structured Outputs (как в ai_client_gpt5.py)
    workout_plan_schema = {
        "type": "object",
        "properties": {
            "plan_name": {"type": "string"},
            "duration_weeks": {"type": "integer"},
            "goal": {"type": "string"},
            "weeks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "week_number": {"type": "integer"},
                        "week_focus": {"type": "string"},
                        "days": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "day_number": {"type": "integer"},
                                    "workout_name": {"type": "string"},
                                    "is_rest_day": {"type": "boolean"},
                                    "exercises": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "exercise_slug": {"type": "string"},
                                                "sets": {"type": "integer"},
                                                "reps": {"type": "string"},
                                                "rest_seconds": {"type": "integer"}
                                            },
                                            "required": ["exercise_slug", "sets", "reps", "rest_seconds"],
                                            "additionalProperties": False
                                        }
                                    },
                                    "confidence_task": {"type": "string"}
                                },
                                "required": ["day_number", "workout_name", "is_rest_day", "exercises", "confidence_task"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["week_number", "week_focus", "days"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["plan_name", "duration_weeks", "goal", "weeks"],
        "additionalProperties": False
    }
    
    # Структура API вызова GPT-5 Responses API
    api_call_structure = {
        "model": "gpt-5",
        "input": [
            {
                "role": "developer",
                "content": "You are a professional fitness coach AI. Create a personalized workout plan based on the user's requirements. Generate ALL weeks requested (typically 4-8 weeks). Each week MUST have 7 days. Include rest days as appropriate."
            },
            {
                "role": "user", 
                "content": user_prompt[:500] + "..." if len(user_prompt) > 500 else user_prompt
            }
        ],
        "reasoning": {
            "effort": "minimal"  # Fast response for workout generation
        },
        "text": {
            "verbosity": "low",  # Concise output
            "format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "workout_plan",
                    "strict": True,
                    "schema": workout_plan_schema
                }
            }
        }
    }
    
    print("🚀 СТРУКТУРА API ВЫЗОВА К GPT-5 RESPONSES API")
    print("=" * 70)
    
    print("\n🔧 ПОЛНАЯ СТРУКТУРА ЗАПРОСА:")
    print("-" * 40)
    print("POST https://api.openai.com/v1/responses")
    print("Content-Type: application/json")
    print("Authorization: Bearer sk-proj-...")
    print("\nBody:")
    print(json.dumps(api_call_structure, indent=2, ensure_ascii=False))
    
    print(f"\n📏 РАЗМЕРЫ ДАННЫХ:")
    print("-" * 40)
    print(f"System message: {len(system_prompt)} символов")
    print(f"User prompt: {len(user_prompt)} символов") 
    print(f"JSON Schema: {len(json.dumps(workout_plan_schema))} символов")
    print(f"Общий размер API запроса: ~{len(json.dumps(api_call_structure)) + len(user_prompt)} символов")
    
    print(f"\n🎯 КЛЮЧЕВЫЕ ОСОБЕННОСТИ GPT-5 RESPONSES API:")
    print("-" * 50)
    print("✅ Новый формат с 'input' вместо 'messages'")
    print("✅ Роль 'developer' для системных инструкций") 
    print("✅ Reasoning effort = 'minimal' для быстрого ответа")
    print("✅ Verbosity = 'low' для краткости")
    print("✅ Structured Outputs с JSON Schema")
    print("✅ Strict = True для точного соответствия схеме")
    print("✅ Обязательный параметр 'name' в json_schema")
    
    print(f"\n🔄 ПРОЦЕСС ОБРАБОТКИ:")
    print("-" * 40)
    print("1. 🧠 AI получает системную роль (developer)")
    print("2. 📝 AI обрабатывает пользовательский запрос")
    print("3. ⚡ Minimal reasoning для скорости")
    print("4. 📋 Генерация ответа по строгой JSON схеме")
    print("5. ✅ Автоматическая валидация структуры")
    print("6. 📤 Возврат структурированного JSON")
    
    print(f"\n💡 ПРЕИМУЩЕСТВА НОВОГО ПОДХОДА:")
    print("-" * 40)
    print("• Гарантированный валидный JSON (no parsing errors)")
    print("• Быстрый ответ с minimal reasoning")
    print("• Четкое разделение ролей (developer vs user)")
    print("• Контроль уровня детализации (verbosity)")
    print("• Строгое соответствие схеме (strict = True)")
    
    print(f"\n🔄 ЧТО ПРОИСХОДИТ ПОСЛЕ API ВЫЗОВА:")
    print("-" * 45)
    print("1. response = client.responses.create(**api_params)")
    print("2. Извлечение content из response.output[].content[]")
    print("3. JSON.parse() - гарантированно валидный")
    print("4. Дополнительная валидация через schemas.py")
    print("5. Создание Django моделей (WorkoutPlan, DailyWorkout, etc.)")
    print("6. Сохранение в базу данных")
    print("7. Редирект пользователя в dashboard")

def show_fallback_scenarios():
    """Показывает сценарии фоллбека"""
    print(f"\n⚠️ СЦЕНАРИИ ФОЛЛБЕКА (если GPT-5 не работает):")
    print("=" * 60)
    
    fallback_flow = [
        "1. 🤖 GPT-5 Responses API fail → FallbackService.generate_default_workout_plan()",
        "2. 📋 Используется предзаготовленный шаблон по уровню опыта",
        "3. 🔄 Подстановка упражнений с приоритетом по мышечным группам",
        "4. ✅ Валидация через те же схемы (guarantee consistency)",
        "5. 💾 Сохранение в БД как обычно",
        "6. 📱 Уведомление пользователя о временном режиме",
        "",
        "🚨 Если и фоллбек не работает:",
        "7. EmergencyWorkoutService.create_emergency_workout()",
        "8. Минимальный план: push_ups, squats, plank",
        "9. 2-недельный базовый цикл",
        "10. Текстовые инструкции без видео (VideoFallbackService)"
    ]
    
    for step in fallback_flow:
        print(step)

if __name__ == "__main__":
    show_gpt5_api_structure()
    show_fallback_scenarios()