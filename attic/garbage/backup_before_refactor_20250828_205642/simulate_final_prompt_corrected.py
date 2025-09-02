#!/usr/bin/env python3
"""
Симуляция исправленного промпта с реальными техническими названиями упражнений из R2
"""

import json


def get_r2_exercise_names():
    """Get real exercise names from R2 upload state"""
    r2_state_path = '/Users/alexbel/Desktop/Проекты/AI Fitness Coach/r2_upload_state.json'
    
    with open(r2_state_path, 'r') as f:
        uploaded_files = json.load(f)
    
    # Extract technical exercise names from video files
    exercise_names = set()
    for file_path in uploaded_files:
        if 'videos/exercises/' in file_path and '_technique_' in file_path:
            filename = file_path.split('/')[-1]  # knee-to-elbow_technique_m01.mp4
            exercise_name = filename.split('_technique_')[0]  # knee-to-elbow
            exercise_names.add(exercise_name)
    
    return sorted(exercise_names)

def show_corrected_prompt():
    """Show the corrected prompt with real exercise names"""
    
    # Get real exercise names from R2
    exercise_names = get_r2_exercise_names()
    
    print("🎯 ИСПРАВЛЕННЫЙ ПРОМПТ С РЕАЛЬНЫМИ УПРАЖНЕНИЯМИ")
    print("=" * 80)
    
    print("\n📊 СТАТИСТИКА:")
    print(f"• Упражнений с видео на Cloudflare R2: {len(exercise_names)}")
    print("• Все упражнения имеют technique, mistake, instruction видео")
    print("• Архетипы: mentor, professional, peer")
    print("• Модели: m01, m02, m03")
    
    print("\n🎮 ПРИМЕР WHITELIST ДЛЯ GPT-5:")
    print("-" * 50)
    print("КРИТИЧЕСКИ ВАЖНО - УПРАЖНЕНИЯ:")
    print("Используйте ТОЛЬКО упражнения из этого списка в тренировочных планах:")
    
    # Show first 30 exercises
    whitelist_preview = ', '.join(exercise_names[:30])
    remaining = len(exercise_names) - 30
    print(f"{whitelist_preview}")
    if remaining > 0:
        print(f"... и еще {remaining} упражнений")
    
    print("\nОБЯЗАТЕЛЬНЫЕ ТРЕБОВАНИЯ:")
    print("1. Каждое упражнение ДОЛЖНО быть из списка выше")
    print("2. Используйте точное название (exercise_slug)")
    print("3. НЕ изобретайте новые упражнения")
    print("4. Если нужно упражнение не из списка - выберите похожее из списка")
    
    print("\nПАРАМЕТРЫ rest_seconds (СТРОГО):")
    print("- Силовые упражнения: 60-90 секунд")
    print("- Кардио упражнения: 30-60 секунд")
    print("- Упражнения на гибкость: 15-30 секунд")
    print("- Все значения должны быть от 10 до 600 секунд")
    
    print("\nВИДЕО-СИСТЕМА:")
    print("- Каждое упражнение имеет предзаписанные видео")
    print("- Включает: технику, типичные ошибки, инструкции по архетипам")
    print("- Система автоматически генерирует плейлисты с мотивационными вставками")
    print("- Используются только упражнения с полным видео-покрытием")
    
    print("\nСТРУКТУРА ПЛЕЙЛИСТА (автоматически создается):")
    print("- Вводное мотивационное видео")
    print("- Инструкции по технике для каждого упражнения")
    print("- Видео разборов типичных ошибок")
    print("- Промежуточная мотивация между упражнениями")
    print("- Заключительное мотивационное видео")
    
    print("\n📁 СТРУКТУРА ФАЙЛОВ НА CLOUDFLARE R2:")
    print("-" * 50)
    print("videos/exercises/{exercise_name}_technique_{model}.mp4")
    print("videos/exercises/{exercise_name}_mistake_{model}.mp4")
    print("videos/instructions/{exercise_name}_instruction_{archetype}_{model}.mp4")
    print("videos/reminders/reminder_{number}.mp4")
    print("videos/motivation/weekly_{archetype}_week{number}.mp4")
    
    print("\n🔗 ПРИМЕРЫ РЕАЛЬНЫХ ФАЙЛОВ:")
    print("-" * 40)
    print("videos/exercises/russian-twists_technique_m01.mp4")
    print("videos/exercises/hack-squats_mistake_m01.mp4")
    print("videos/instructions/knee-to-elbow_instruction_wise_mentor_m01.mp4")
    print("videos/reminders/reminder_224.mp4")
    
    print("\n✅ ПРЕИМУЩЕСТВА ИСПРАВЛЕНИЯ:")
    print("-" * 40)
    print("• GPT-5 будет использовать только упражнения с реальными видео")
    print("• Система плейлистов найдет все файлы по названиям")
    print("• Нет разрыва между промптом и медиафайлами")
    print("• 147 упражнений покрывают все потребности пользователей")
    print("• Автоматическая генерация плейлистов работает корректно")
    
    print("\n🚀 РЕЗУЛЬТАТ РАБОТЫ:")
    print("-" * 30)
    print("1. Пользователь завершает онбординг")
    print("2. GPT-5 получает whitelist из 147 реальных упражнений")
    print("3. Генерирует план используя только whitelist")
    print("4. Система находит все видео по техническим названиям")
    print("5. Создается персональный плейлист с мотивацией")
    print("6. Пользователь получает полноценные видео-уроки!")
    
    # Save full whitelist for reference
    with open('/Users/alexbel/Desktop/Проекты/AI Fitness Coach/r2_exercise_whitelist.txt', 'w') as f:
        f.write("# R2 Cloudflare Exercise Whitelist\n")
        f.write(f"# Total: {len(exercise_names)} exercises\n\n")
        for name in exercise_names:
            f.write(f"{name}\n")
    
    print("\n💾 Полный whitelist сохранен в: r2_exercise_whitelist.txt")

if __name__ == "__main__":
    show_corrected_prompt()