#!/usr/bin/env python3
"""
Анализ идеального плейлиста на один день тренировки
Основано на структуре 616 видео: 271 упражнений + 345 мотивационных
"""

def analyze_video_structure():
    """Анализ структуры видео"""
    print("📊 СТРУКТУРА НАШИХ 616 ВИДЕО")
    print("=" * 60)
    
    print("\n💪 УПРАЖНЕНИЯ (271 видео - ОДНА модель):")
    exercises = {
        'Разминка': 42,
        'Основные': 145,  # 105 базовых + 40 дополнительных
        'Сексуальная выносливость': 42,
        'Расслабление': 42
    }
    
    for category, count in exercises.items():
        print(f"  - {category}: {count} видео")
    
    print(f"\n  📈 Итого упражнений: {sum(exercises.values())} видео")
    
    print("\n🎤 МОТИВАЦИОННЫЕ (345 видео - ТРИ тренера):")
    motivational = {
        'Вступление и приветствие': 63,      # 21 день × 3 тренера
        'Мотивация после разминки': 63,      # 21 день × 3 тренера  
        'Мотивация после основных': 63,      # 21 день × 3 тренера
        'Мотивирующий ролик тренера': 63,    # 21 день × 3 тренера
        'Напутственное слово': 63,           # 21 день × 3 тренера
        'Еженедельные длинные': 18,          # 6 недель × 3 тренера
        'Двухнедельные прогресс': 9,         # 3 раза × 3 тренера
        'Финальное видео курса': 3           # 3 тренера
    }
    
    for category, count in motivational.items():
        print(f"  - {category}: {count} видео")
    
    print(f"\n  📈 Итого мотивационных: {sum(motivational.values())} видео")
    print(f"\n🎯 ОБЩИЙ ИТОГ: {sum(exercises.values()) + sum(motivational.values())} видео")

def create_ideal_daily_playlist():
    """Создание идеального плейлиста на один день"""
    print("\n\n📋 ИДЕАЛЬНЫЙ ПЛЕЙЛИСТ НА ОДИН ДЕНЬ")
    print("=" * 60)
    
    # Структура одного дня тренировки
    playlist_structure = [
        # Блок 1: Начало тренировки
        {
            'order': 1,
            'video_type': 'motivational',
            'category': 'intro',
            'title': 'Вступление и приветствие',
            'performer': 'Тренер (по архетипу)',
            'duration_min': 2,
            'content': 'Приветствие, настрой на тренировку'
        },
        
        # Блок 2: Разминка
        {
            'order': 2,
            'video_type': 'exercise',
            'category': 'warmup',
            'title': 'Разминка упражнение 1',
            'performer': 'Модель',
            'duration_min': 3.25,  # 3 подхода × 15 повторов
            'content': 'Подготовка мышц к нагрузке'
        },
        {
            'order': 3,
            'video_type': 'exercise', 
            'category': 'warmup',
            'title': 'Разминка упражнение 2',
            'performer': 'Модель',
            'duration_min': 3.25,
            'content': 'Активация суставов и связок'
        },
        {
            'order': 4,
            'video_type': 'motivational',
            'category': 'after_warmup',
            'title': 'Мотивация после разминки',
            'performer': 'Тренер (по архетипу)',
            'duration_min': 2,
            'content': 'Подготовка к основной части'
        },
        
        # Блок 3: Основные упражнения
        {
            'order': 5,
            'video_type': 'exercise',
            'category': 'main',
            'title': 'Основное упражнение 1',
            'performer': 'Модель',
            'duration_min': 3.25,
            'content': 'Силовая нагрузка - группа мышц 1'
        },
        {
            'order': 6,
            'video_type': 'exercise',
            'category': 'main', 
            'title': 'Основное упражнение 2',
            'performer': 'Модель',
            'duration_min': 3.25,
            'content': 'Силовая нагрузка - группа мышц 2'
        },
        {
            'order': 7,
            'video_type': 'exercise',
            'category': 'main',
            'title': 'Основное упражнение 3', 
            'performer': 'Модель',
            'duration_min': 3.25,
            'content': 'Силовая нагрузка - группа мышц 3'
        },
        {
            'order': 8,
            'video_type': 'exercise',
            'category': 'main',
            'title': 'Основное упражнение 4',
            'performer': 'Модель', 
            'duration_min': 3.25,
            'content': 'Силовая нагрузка - группа мышц 4'
        },
        {
            'order': 9,
            'video_type': 'exercise',
            'category': 'main',
            'title': 'Основное упражнение 5',
            'performer': 'Модель',
            'duration_min': 3.25,
            'content': 'Силовая нагрузка - группа мышц 5'
        },
        {
            'order': 10,
            'video_type': 'motivational',
            'category': 'after_main',
            'title': 'Мотивация после основных',
            'performer': 'Тренер (по архетипу)',
            'duration_min': 2,
            'content': 'Похвала, переход к спец. упражнениям'
        },
        
        # Блок 4: Сексуальная выносливость
        {
            'order': 11,
            'video_type': 'exercise',
            'category': 'endurance',
            'title': 'Сексуальная выносливость упр. 1',
            'performer': 'Модель',
            'duration_min': 3.25,
            'content': 'Специальные упражнения для выносливости'
        },
        {
            'order': 12,
            'video_type': 'exercise',
            'category': 'endurance', 
            'title': 'Сексуальная выносливость упр. 2',
            'performer': 'Модель',
            'duration_min': 3.25,
            'content': 'Укрепление специфических мышц'
        },
        {
            'order': 13,
            'video_type': 'motivational',
            'category': 'motivating_speech',
            'title': 'Мотивирующий ролик тренера',
            'performer': 'Тренер (по архетипу)',
            'duration_min': 2,
            'content': 'Мотивация на финишную прямую'
        },
        
        # Блок 5: Завершение
        {
            'order': 14,
            'video_type': 'exercise',
            'category': 'cooldown',
            'title': 'Расслабление упражнение 1',
            'performer': 'Модель',
            'duration_min': 3.25,
            'content': 'Растяжка и релаксация'
        },
        {
            'order': 15,
            'video_type': 'exercise',
            'category': 'cooldown',
            'title': 'Расслабление упражнение 2', 
            'performer': 'Модель',
            'duration_min': 3.25,
            'content': 'Восстановление и дыхание'
        },
        {
            'order': 16,
            'video_type': 'motivational',
            'category': 'farewell',
            'title': 'Напутственное слово',
            'performer': 'Тренер (по архетипу)',
            'duration_min': 2,
            'content': 'Поздравление с завершением дня'
        }
    ]
    
    print("\n🎬 ПОСЛЕДОВАТЕЛЬНОСТЬ ВИДЕО В ПЛЕЙЛИСТЕ:")
    print("-" * 80)
    
    total_duration = 0
    exercise_count = 0
    motivational_count = 0
    
    for item in playlist_structure:
        duration_str = f"{item['duration_min']:.2f} мин"
        print(f"{item['order']:2d}. {item['title']:<35} | {item['performer']:<20} | {duration_str}")
        
        total_duration += item['duration_min']
        if item['video_type'] == 'exercise':
            exercise_count += 1
        else:
            motivational_count += 1
    
    print("-" * 80)
    print(f"📊 СТАТИСТИКА ПЛЕЙЛИСТА:")
    print(f"   💪 Упражнений: {exercise_count} видео")
    print(f"   🎤 Мотивационных: {motivational_count} видео")
    print(f"   ⏱️  Общая длительность: {total_duration:.1f} минут ({total_duration/60:.1f} часа)")
    
    return playlist_structure

def analyze_special_videos():
    """Анализ специальных видео (еженедельных, двухнедельных, финальных)"""
    print("\n\n🎯 СПЕЦИАЛЬНЫЕ ВИДЕО ДЛЯ ОСОБЫХ ДНЕЙ")
    print("=" * 60)
    
    special_videos = [
        {
            'type': 'weekly',
            'name': 'Еженедельные видео',
            'frequency': 'Каждое воскресенье',
            'duration': '10 минут',
            'count': '18 видео (6 недель × 3 тренера)',
            'purpose': 'Подведение итогов недели, мотивация на следующую'
        },
        {
            'type': 'biweekly', 
            'name': 'Двухнедельные прогресс-видео',
            'frequency': 'Каждые 2 недели',
            'duration': '15 минут',
            'count': '9 видео (3 раза × 3 тренера)', 
            'purpose': 'Анализ прогресса, корректировка плана'
        },
        {
            'type': 'final',
            'name': 'Финальные видео курса',
            'frequency': 'По завершению курса',
            'duration': '10-15 минут',
            'count': '3 видео (по одному от каждого тренера)',
            'purpose': 'Поздравление с завершением, дальнейшие рекомендации'
        }
    ]
    
    for video in special_videos:
        print(f"\n📅 {video['name']}:")
        print(f"   🔄 Частота: {video['frequency']}")
        print(f"   ⏱️  Длительность: {video['duration']}")
        print(f"   📊 Количество: {video['count']}")
        print(f"   🎯 Назначение: {video['purpose']}")

def main():
    """Основная функция анализа"""
    print("🔍 АНАЛИЗ ИДЕАЛЬНОГО ПЛЕЙЛИСТА ДЛЯ AI FITNESS COACH")
    print("=" * 80)
    
    # Анализируем структуру видео
    analyze_video_structure()
    
    # Создаем идеальный плейлист
    playlist = create_ideal_daily_playlist()
    
    # Анализируем специальные видео
    analyze_special_videos()
    
    print(f"\n\n✅ АНАЛИЗ ЗАВЕРШЕН!")
    print("Структура идеального плейлиста определена на основе 616 загруженных видео.")

if __name__ == "__main__":
    main()