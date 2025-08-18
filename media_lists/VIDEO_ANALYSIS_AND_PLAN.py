#!/usr/bin/env python3
"""
Анализ имеющихся видео и план переименования для AI Fitness Coach
Основано на изучении кода приложения и доступных материалов
"""

import os
import json
from datetime import datetime

def analyze_video_usage():
    """Анализ использования видео в приложении на основе изученного кода"""
    
    # Структура использования видео в приложении
    video_usage = {
        "technique": {
            "description": "Видео демонстрации техники выполнения упражнений",
            "naming_pattern": "{exercise_slug}_technique_{model}.mp4", 
            "model_requirement": "mod1 (основная модель для техники)",
            "duration_target": "30-60 секунд",
            "content": "Демонстрация правильной техники выполнения упражнения",
            "needed_per_exercise": 1,
            "total_needed": 144  # По новой базе упражнений
        },
        
        "instruction": {
            "description": "Инструктаж от тренеров разных архетипов",
            "naming_pattern": "{exercise_slug}_instruction_{archetype}_{model}.mp4",
            "archetypes": ["bro", "sergeant", "intellectual"],
            "models": ["mod1", "mod2", "mod3"], 
            "duration_target": "20-40 секунд",
            "content": "Мотивирующие инструкции для выполнения упражнения",
            "needed_per_exercise": 9, # 3 архетипа × 3 модели
            "total_needed": 1296  # 144 упражнения × 9 комбинаций
        },
        
        "reminder": {
            "description": "Напоминания и подбадривания во время выполнения",
            "naming_pattern": "{exercise_slug}_reminder_{archetype}_{number}.mp4",
            "archetypes": ["bro", "sergeant", "intellectual"],
            "duration_target": "10-20 секунд", 
            "content": "Короткие мотивирующие фразы и напоминания",
            "needed_per_exercise": 9, # 3 архетипа × 3 напоминания
            "total_needed": 1296  # 144 упражнения × 9 напоминаний
        },
        
        "weekly": {
            "description": "Еженедельные мотивационные видео",
            "naming_pattern": "weekly_{archetype}_week{number}.mp4",
            "archetypes": ["bro", "sergeant", "intellectual"],
            "weeks": list(range(1, 9)),  # До 8 недель
            "duration_target": "2-5 минут",
            "content": "Мотивация и поздравления за прогресс",
            "needed_per_archetype": 8,
            "total_needed": 24  # 3 архетипа × 8 недель
        },
        
        "final": {
            "description": "Финальные поздравления по завершению программы",
            "naming_pattern": "final_{archetype}.mp4",
            "archetypes": ["bro", "sergeant", "intellectual"],
            "duration_target": "3-7 минут",
            "content": "Торжественное поздравление с завершением программы",
            "needed_per_archetype": 1,
            "total_needed": 3  # 3 архетипа
        }
    }
    
    return video_usage

def analyze_available_materials():
    """Анализ доступных материалов на диске Z9"""
    
    materials = {
        "trainer_1": {
            "path": "/Volumes/Z9/материалы для ai fitnes/trainer 1/Videos",
            "count": 429,
            "format": "mp4",
            "naming": "timestamp format (20200430_192750.mp4)",
            "description": "Модель 1 - архетип 'bro' (братский подход)"
        },
        
        "trainer_2": {
            "path": "/Volumes/Z9/материалы для ai fitnes/trainer 2", 
            "count": 294,
            "format": "mp4",
            "naming": "Dennis Dillon series",
            "description": "Модель 2 - архетип 'sergeant' (сержантский подход)"
        },
        
        "trainer_3": {
            "path": "/Volumes/Z9/материалы для ai fitnes/trainer 3",
            "count": 65,
            "format": "mp4", 
            "naming": "GromBurja series",
            "description": "Модель 3 - архетип 'intellectual' (интеллектуальный подход)"
        },
        
        "long_videos": {
            "path": "/Volumes/Z9/материалы для ai fitnes/long and weekly videos",
            "count": 245,
            "format": "mp4",
            "naming": "descriptive names",
            "description": "Длинные видео для еженедельных и финальных мотиваций"
        },
        
        "exercises_content": {
            "path": "/Volumes/Z9/материалы для ai fitnes/exercises",
            "note": "Не подходит для упражнений - это контент для взрослых, используется как заглушки",
            "description": "Тестовые видео моделей из соцсетей"
        }
    }
    
    return materials

def create_video_mapping_plan():
    """Создание плана маппинга видео согласно потребностям приложения"""
    
    plan = {
        "archetype_mapping": {
            "bro": {
                "source": "trainer_1",
                "personality": "Дружелюбный, поддерживающий, как лучший друг",
                "tone": "Неформальный, мотивирующий",
                "examples": ["Давай, братан!", "Ты можешь!", "Отличная работа!"]
            },
            "sergeant": {
                "source": "trainer_2", 
                "personality": "Строгий, требовательный, дисциплинированный",
                "tone": "Четкий, командный",
                "examples": ["Выполняй!", "Без поблажек!", "Дисциплина!"]
            },
            "intellectual": {
                "source": "trainer_3",
                "personality": "Мудрый, объясняющий, научный подход",
                "tone": "Спокойный, образовательный", 
                "examples": ["Помни о технике", "Научно доказано", "Осознанное движение"]
            }
        },
        
        "video_duration_requirements": {
            "technique": "30-60 сек - демонстрация упражнения",
            "instruction": "20-40 сек - мотивирующий инструктаж",
            "reminder": "10-20 сек - короткие подбадривания", 
            "weekly": "2-5 мин - еженедельная мотивация",
            "final": "3-7 мин - финальное поздравление"
        },
        
        "prioritization": {
            "phase_1": {
                "focus": "Базовые упражнения с техникой (mod1)",
                "videos_needed": 144,
                "source": "trainer_1 (429 доступно)",
                "pattern": "{exercise_slug}_technique_mod1.mp4"
            },
            "phase_2": {
                "focus": "Инструкции от всех архетипов", 
                "videos_needed": 432,  # 144 упражнения × 3 архетипа
                "source": "все тренеры",
                "pattern": "{exercise_slug}_instruction_{archetype}_mod{1-3}.mp4"
            },
            "phase_3": {
                "focus": "Напоминания",
                "videos_needed": 432,  # 144 упражнения × 3 архетипа
                "source": "все тренеры", 
                "pattern": "{exercise_slug}_reminder_{archetype}_{1-3}.mp4"
            },
            "phase_4": {
                "focus": "Еженедельные мотивации",
                "videos_needed": 24,  # 3 архетипа × 8 недель
                "source": "long_videos",
                "pattern": "weekly_{archetype}_week{1-8}.mp4"
            },
            "phase_5": {
                "focus": "Финальные поздравления", 
                "videos_needed": 3,  # 3 архетипа
                "source": "long_videos",
                "pattern": "final_{archetype}.mp4"
            }
        }
    }
    
    return plan

def calculate_video_requirements():
    """Расчет требований к видео"""
    
    # Загружаем данные о современных упражнениях
    exercise_categories = {
        "movement_prep": 12,
        "fundamental_patterns": 45, 
        "power_explosive": 15,
        "primal_flow": 25,
        "corrective_therapeutic": 20,
        "mindful_movement": 15,
        "recovery_regeneration": 12
    }
    
    total_exercises = sum(exercise_categories.values())  # 144
    
    requirements = {
        "total_exercises": total_exercises,
        "video_types": {
            "technique": {
                "per_exercise": 1,
                "total": total_exercises * 1,  # 144
                "duration_each": "30-60 сек"
            },
            "instruction": {
                "per_exercise": 9,  # 3 архетипа × 3 модели
                "total": total_exercises * 9,  # 1296
                "duration_each": "20-40 сек"
            },
            "reminder": {
                "per_exercise": 9,  # 3 архетипа × 3 напоминания
                "total": total_exercises * 9,  # 1296
                "duration_each": "10-20 сек"
            },
            "weekly": {
                "per_week": 3,  # 3 архетипа
                "weeks": 8,
                "total": 3 * 8,  # 24
                "duration_each": "2-5 мин"
            },
            "final": {
                "per_archetype": 1,
                "total": 3,  # 3 архетипа
                "duration_each": "3-7 мин"
            }
        },
        "grand_total": 144 + 1296 + 1296 + 24 + 3,  # 2763 видео
        "available_materials": {
            "trainer_1": 429,
            "trainer_2": 294, 
            "trainer_3": 65,
            "long_videos": 245,
            "total_available": 429 + 294 + 65 + 245  # 1033 видео
        },
        "coverage_analysis": {
            "sufficient_for_phase_1": True,  # 144 нужно, 429 доступно от trainer_1
            "sufficient_for_full_system": False,  # 2763 нужно, 1033 доступно
            "recommended_approach": "Поэтапное внедрение с приоритизацией"
        }
    }
    
    return requirements

def generate_chatgpt_naming_system():
    """Генерация системы именования для ChatGPT интеграции"""
    
    naming_system = {
        "principles": [
            "Понятные названия для ChatGPT",
            "Структурированный формат",
            "Легкая автоматизация",
            "Соответствие базе упражнений"
        ],
        
        "patterns": {
            "technique": {
                "format": "{exercise_slug}_technique_mod1.mp4",
                "example": "quality-push-up_technique_mod1.mp4",
                "chatgpt_description": "Видео демонстрации техники упражнения"
            },
            "instruction": {
                "format": "{exercise_slug}_instruction_{archetype}_mod{number}.mp4", 
                "example": "quality-push-up_instruction_bro_mod1.mp4",
                "chatgpt_description": "Инструктаж от тренера определенного архетипа"
            },
            "reminder": {
                "format": "{exercise_slug}_reminder_{archetype}_{number}.mp4",
                "example": "quality-push-up_reminder_bro_1.mp4", 
                "chatgpt_description": "Мотивирующее напоминание во время упражнения"
            },
            "weekly": {
                "format": "weekly_{archetype}_week{number}.mp4",
                "example": "weekly_bro_week3.mp4",
                "chatgpt_description": "Еженедельная мотивация от тренера"
            },
            "final": {
                "format": "final_{archetype}.mp4",
                "example": "final_intellectual.mp4", 
                "chatgpt_description": "Финальное поздравление с завершением программы"
            }
        },
        
        "archetype_codes": {
            "bro": "Дружелюбный тренер-приятель",
            "sergeant": "Строгий тренер-сержант", 
            "intellectual": "Мудрый тренер-интеллектуал"
        },
        
        "model_codes": {
            "mod1": "Основная модель (trainer_1)",
            "mod2": "Вторая модель (trainer_2)",
            "mod3": "Третья модель (trainer_3)"
        },
        
        "cloudflare_integration": {
            "base_url": "https://ai-fitness-media.r2.cloudflarestorage.com",
            "folder_structure": {
                "exercises": "videos/exercises/",
                "instructions": "videos/instructions/", 
                "reminders": "videos/reminders/",
                "weekly": "videos/weekly/",
                "final": "videos/final/"
            },
            "example_full_url": "https://ai-fitness-media.r2.cloudflarestorage.com/videos/exercises/quality-push-up_technique_mod1.mp4"
        }
    }
    
    return naming_system

def save_analysis():
    """Сохранение полного анализа"""
    
    analysis = {
        "timestamp": datetime.now().isoformat(),
        "video_usage": analyze_video_usage(),
        "available_materials": analyze_available_materials(),
        "mapping_plan": create_video_mapping_plan(),
        "requirements": calculate_video_requirements(),
        "naming_system": generate_chatgpt_naming_system()
    }
    
    # Сохраняем анализ
    output_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/VIDEO_ANALYSIS_COMPLETE.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Полный анализ видео сохранен: {output_file}")
    
    # Создаем краткий отчет
    summary = create_summary_report(analysis)
    summary_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/VIDEO_PLAN_SUMMARY.md'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"📋 Краткий план сохранен: {summary_file}")
    
    return analysis

def create_summary_report(analysis):
    """Создание краткого отчета"""
    
    req = analysis['requirements']
    
    summary = f"""# План работы с видео AI Fitness Coach

## 📊 Анализ потребностей

### Всего упражнений в новой базе: {req['total_exercises']}

### Требования к видео:
- **Техника**: {req['video_types']['technique']['total']} видео (30-60 сек каждое)
- **Инструкции**: {req['video_types']['instruction']['total']} видео (20-40 сек каждое)  
- **Напоминания**: {req['video_types']['reminder']['total']} видео (10-20 сек каждое)
- **Еженедельные**: {req['video_types']['weekly']['total']} видео (2-5 мин каждое)
- **Финальные**: {req['video_types']['final']['total']} видео (3-7 мин каждое)

**ИТОГО: {req['grand_total']} видео**

## 📁 Доступные материалы

- Trainer 1 (bro): {req['available_materials']['trainer_1']} видео
- Trainer 2 (sergeant): {req['available_materials']['trainer_2']} видео  
- Trainer 3 (intellectual): {req['available_materials']['trainer_3']} видео
- Длинные видео: {req['available_materials']['long_videos']} видео

**ИТОГО: {req['available_materials']['total_available']} видео**

## 🎯 Поэтапный план

### Фаза 1: Базовая техника (ПРИОРИТЕТ)
- Нужно: 144 видео техники
- Доступно: 429 от trainer_1
- ✅ **Реализуемо**

### Фаза 2: Инструкции
- Нужно: 432 видео (144 × 3 архетипа) 
- Доступно: 788 от всех тренеров
- ✅ **Реализуемо**

### Фаза 3: Напоминания  
- Нужно: 432 видео
- Доступно: остаток после фазы 2
- ⚠️ **Частично реализуемо**

### Фаза 4: Еженедельные
- Нужно: 24 видео
- Источник: длинные видео (245 доступно)
- ✅ **Реализуемо**

### Фаза 5: Финальные
- Нужно: 3 видео
- Источник: длинные видео
- ✅ **Реализуемо**

## 📝 Система именования

### Для упражнений:
- Техника: `{{exercise_slug}}_technique_mod1.mp4`
- Инструкция: `{{exercise_slug}}_instruction_{{archetype}}_mod{{n}}.mp4`
- Напоминание: `{{exercise_slug}}_reminder_{{archetype}}_{{n}}.mp4`

### Для мотивации:
- Еженедельные: `weekly_{{archetype}}_week{{n}}.mp4`
- Финальные: `final_{{archetype}}.mp4`

### Архетипы:
- `bro` - дружелюбный приятель (trainer_1)
- `sergeant` - строгий сержант (trainer_2)  
- `intellectual` - мудрый интеллектуал (trainer_3)

## 🚀 Рекомендации

1. **Начать с Фазы 1** - создать 144 видео техники
2. **Использовать автоматизацию** для массового переименования
3. **Поэтапная загрузка** на Cloudflare R2
4. **Тестирование** с ChatGPT интеграцией
5. **Постепенное расширение** функционала

## 📍 Структура папок на Z9

```
/Volumes/Z9/AI_FITNESS_COACH_VIDEOS/
├── exercises/          # Техника выполнения
├── instructions/       # Инструктажи  
├── reminders/         # Напоминания
├── weekly/            # Еженедельные мотивации
└── final/             # Финальные поздравления
```

## ⚡ Интеграция с ChatGPT

Система именования позволит ChatGPT:
- Легко находить нужные видео по названию упражнения
- Выбирать архетип тренера по пользователю
- Формировать плейлисты автоматически
- Адаптировать контент под прогресс пользователя
"""

    return summary

if __name__ == '__main__':
    analysis = save_analysis()
    print("📋 Анализ завершен!")
    print(f"📊 Всего видео нужно: {analysis['requirements']['grand_total']}")
    print(f"💾 Всего доступно: {analysis['requirements']['available_materials']['total_available']}")
    print(f"✅ Достаточно для базового функционала: {analysis['requirements']['coverage_analysis']['sufficient_for_phase_1']}")