#!/usr/bin/env python3
"""
Modern Exercise Database 2025 - AI Fitness Coach
Based on current fitness trends: Animal Flow, Functional Movement, Mind-Body Integration
"""

import pandas as pd
from datetime import datetime

def create_modern_exercises_database():
    """Create modern exercise database aligned with 2024-2025 fitness trends"""
    
    exercises = []
    exercise_id = 1
    
    # === MOVEMENT PREPARATION (12 упражнений) ===
    movement_prep = [
        ("Дыхательная активация", "Breathing Activation", "Диафрагмальное дыхание с активацией глубоких мышц кора. Подготавливает нервную систему к движению.", "mobility_breathwork"),
        ("Нейромышечная разминка", "Neuromuscular Warm-up", "Последовательная активация основных двигательных паттернов с акцентом на качество движения.", "movement_preparation"), 
        ("Мобилизация позвоночника", "Spinal Wave", "Волнообразные движения позвоночника от шеи до таза. Активирует сегментарную подвижность.", "mobility_flow"),
        ("Активация ягодиц", "Glute Activation Flow", "Серия движений для активации ягодичных мышц и стабилизации таза.", "activation"),
        ("Подготовка плеч", "Shoulder Mobility Flow", "Комплекс для мобилизации плечевого пояса и активации стабилизаторов.", "mobility_preparation"),
        ("Активация стоп", "Foot Activation", "Работа с подвижностью и силой стоп для улучшения проприоцепции.", "foundation_prep"),
        ("Пробуждение фасций", "Fascial Wake-up", "Движения для активации фасциальных цепей и улучшения тканевого скольжения.", "fascial_release"),
        ("Координационная подготовка", "Coordination Primer", "Простые упражнения на координацию и баланс для подготовки нервной системы.", "neural_prep"),
        ("Темповая синхронизация", "Rhythmic Synchronization", "Движения в заданном темпе для синхронизации дыхания и движения.", "rhythm_flow"),
        ("Суставная мобилизация", "Joint Mobility Sequence", "Последовательная мобилизация всех основных суставов тела.", "joint_mobility"),
        ("Активация кора", "Core Connection", "Упражнения для осознанной активации глубоких мышц кора.", "core_activation"),
        ("Интеграция движения", "Movement Integration", "Соединение дыхания, осознанности и базовых движений.", "integration_prep")
    ]
    
    for i, (name_ru, name_en, description, subcategory) in enumerate(movement_prep):
        exercises.append({
            'id': exercise_id,
            'name_ru': name_ru,
            'name_en': name_en,
            'description': description,
            'category': 'movement_prep',
            'category_ru': 'Подготовка к движению',
            'subcategory': subcategory,
            'muscle_groups': ['full_body', 'core'],
            'difficulty': 'beginner',
            'equipment': [],
            'duration_seconds': 60,
            'mental_component': True,
            'breathing_pattern': 'integrated',
            'movement_plane': 'multi_planar',
            'slug': name_en.lower().replace(' ', '-').replace("'", ''),
            'file_name': f"movement_prep_{i+1:02d}_technique_m01.mp4",
            'display_title': name_ru,
            'sets': 1,
            'reps': '1-2 мин',
            'rest_seconds': 15
        })
        exercise_id += 1
    
    # === FUNDAMENTAL PATTERNS (45 упражнений) ===
    fundamental_patterns = [
        # Squat Patterns (8 exercises)
        ("Приседание с оценкой", "Assessment Squat", "Базовое приседание с акцентом на выявление дисбалансов и ограничений подвижности.", "squat_pattern"),
        ("Приседание гоблет", "Goblet Squat Hold", "Глубокое приседание с удержанием позиции для развития подвижности.", "squat_pattern"),
        ("Приседание на одной ноге", "Single Leg Squat", "Функциональное приседание на одной ноге для развития силы и стабильности.", "squat_pattern"),
        ("Приседание с ротацией", "Squat to Rotation", "Приседание с поворотом корпуса для развития многоплоскостной подвижности.", "squat_pattern"),
        ("Реактивное приседание", "Reactive Squat", "Приседание с изменением направления для развития реакции.", "squat_pattern"),
        ("Приседание-переход", "Transition Squat", "Приседание как переходное движение между позициями.", "squat_pattern"),
        ("Приседание с дыханием", "Breathing Squat", "Медленное приседание с акцентом на дыхательный паттерн.", "squat_pattern"),
        ("Приседание казак", "Cossack Squat", "Боковое приседание для развития латеральной подвижности.", "squat_pattern"),
        
        # Push Patterns (8 exercises)
        ("Отжимание качественное", "Quality Push-up", "Отжимание с акцентом на качество движения и контроль.", "push_pattern"),
        ("Отжимание на одной руке", "Single Arm Push-up Progression", "Прогрессия к отжиманию на одной руке через боковые варианты.", "push_pattern"),
        ("Отжимание мультиплоскостное", "Multi-planar Push-up", "Отжимание с движением в разных плоскостях.", "push_pattern"),
        ("Отжимание-переход", "Push-up Flow", "Отжимание как часть непрерывного движения.", "push_pattern"),
        ("Отжимание пике", "Pike Push-up", "Отжимание в позе пике для развития силы плеч.", "push_pattern"),
        ("Отжимание хинду", "Hindu Push-up", "Динамичное отжимание с волнообразным движением.", "push_pattern"),
        ("Отжимание лучник", "Archer Push-up", "Отжимание с переносом веса на одну сторону.", "push_pattern"),
        ("Отжимание дыхательное", "Breathing Push-up", "Медленное отжимание с интеграцией дыхания.", "push_pattern"),
        
        # Pull Patterns (6 exercises)
        ("Австралийские подтягивания", "Australian Pull-ups", "Горизонтальная тяга для развития мышц спины.", "pull_pattern"),
        ("Тяга лежа", "Prone Pull", "Имитация тяги лежа на животе для активации задней цепи.", "pull_pattern"),
        ("Супермен динамический", "Dynamic Superman", "Динамичный подъем корпуса и рук лежа на животе.", "pull_pattern"),
        ("Ретракция лопаток", "Scapular Retraction", "Изолированная работа с лопатками для улучшения осанки.", "pull_pattern"),
        ("Пловец", "Swimming Pattern", "Имитация плавания для развития координации рук.", "pull_pattern"),
        ("Подтягивание прогрессия", "Pull-up Progression", "Ступенчатая прогрессия к полным подтягиваниям.", "pull_pattern"),
        
        # Hinge Patterns (6 exercises)
        ("Румынская тяга", "Romanian Deadlift", "Тазобедренное сгибание с собственным весом.", "hinge_pattern"),
        ("Добро утро", "Good Morning", "Наклон с прямой спиной для развития задней цепи.", "hinge_pattern"),
        ("Ягодичный мостик", "Hip Bridge Flow", "Подъем таза с различными вариациями.", "hinge_pattern"),
        ("Стол", "Table Top Hold", "Удержание позиции стола для развития задней цепи.", "hinge_pattern"),
        ("Кик назад", "Hip Hinge Kick", "Отведение ноги назад с сохранением нейтрального позвоночника.", "hinge_pattern"),
        ("Маятник", "Hip Pendulum", "Маятниковые движения в тазобедренном суставе.", "hinge_pattern"),
        
        # Lunge Patterns (7 exercises)
        ("Выпад качественный", "Quality Lunge", "Базовый выпад с акцентом на технику и контроль.", "lunge_pattern"),
        ("Выпад реверсивный", "Reverse Lunge", "Шаг назад для снижения нагрузки на колени.", "lunge_pattern"),
        ("Выпад боковой", "Lateral Lunge", "Боковой выпад для развития фронтальной плоскости.", "lunge_pattern"),
        ("Выпад с ротацией", "Rotational Lunge", "Выпад с поворотом для многоплоскостного движения.", "lunge_pattern"),
        ("Выпад часы", "Clock Lunge", "Выпады в разных направлениях как стрелки часов.", "lunge_pattern"),
        ("Выпад-переход", "Lunge Flow", "Выпад как переходное движение между позициями.", "lunge_pattern"),
        ("Выпад с досягаемостью", "Reaching Lunge", "Выпад с активным досягаемостью руками.", "lunge_pattern"),
        
        # Carry Patterns (5 exercises)
        ("Переноска одной рукой", "Single Arm Carry", "Имитация переноски груза одной рукой.", "carry_pattern"),
        ("Фермерская походка", "Farmer's Walk", "Походка с воображаемым грузом в обеих руках.", "carry_pattern"),
        ("Чемоданная походка", "Suitcase Carry", "Антилатеральная стабилизация при односторонней нагрузке.", "carry_pattern"),
        ("Передняя переноска", "Front Loaded Carry", "Переноска воображаемого груза перед собой.", "carry_pattern"),
        ("Переноска над головой", "Overhead Carry", "Удержание рук над головой при ходьбе.", "carry_pattern"),
        
        # Anti-Movement Patterns (5 exercises)
        ("Анти-разгибание", "Anti-Extension", "Планка и вариации для предотвращения разгибания поясницы.", "anti_movement"),
        ("Анти-ротация", "Anti-Rotation", "Паллоф пресс без оборудования для анти-ротации.", "anti_movement"),
        ("Анти-флексия", "Anti-Lateral Flexion", "Боковая планка для предотвращения бокового наклона.", "anti_movement"),
        ("Анти-флексия", "Anti-Flexion", "Супермен для предотвращения сгибания позвоночника.", "anti_movement"),
        ("Интегрированное анти", "Integrated Anti-Movement", "Комбинация анти-движений в одном упражнении.", "anti_movement")
    ]
    
    for i, (name_ru, name_en, description, subcategory) in enumerate(fundamental_patterns):
        difficulty = 'intermediate' if 'Single' in name_en or 'One' in name_en else 'beginner'
        exercises.append({
            'id': exercise_id,
            'name_ru': name_ru,
            'name_en': name_en,
            'description': description,
            'category': 'fundamental_patterns',
            'category_ru': 'Базовые паттерны',
            'subcategory': subcategory,
            'muscle_groups': ['full_body'],
            'difficulty': difficulty,
            'equipment': [],
            'duration_seconds': 45,
            'mental_component': False,
            'breathing_pattern': 'natural',
            'movement_plane': 'multi_planar' if 'Rotation' in name_en or 'Multi' in name_en else 'sagittal',
            'slug': name_en.lower().replace(' ', '-').replace("'", ''),
            'file_name': f"fundamental_{exercise_id-12:03d}_technique_m01.mp4",
            'display_title': name_ru,
            'sets': 3,
            'reps': '8-12',
            'rest_seconds': 45
        })
        exercise_id += 1
    
    # === POWER & EXPLOSIVE (15 упражнений) ===
    power_explosive = [
        ("Прыжок в приседе", "Jump Squat", "Взрывное выпрыгивание из приседа для развития мощности ног.", "plyometric_lower"),
        ("Берпи современный", "Modern Burpee", "Улучшенная версия берпи с акцентом на качество движения.", "full_body_power"),
        ("Прыжки на ящик", "Box Jump Simulation", "Имитация прыжков на ящик с акцентом на приземление.", "plyometric_lower"),
        ("Отжимание плиометрическое", "Plyometric Push-up", "Взрывные отжимания с отрывом рук от пола.", "plyometric_upper"),
        ("Альпинист взрывной", "Explosive Mountain Climber", "Быстрая смена ног в планке с максимальной скоростью.", "full_body_power"),
        ("Броски медбола", "Medicine Ball Slam Simulation", "Имитация бросков медбола для развития мощности кора.", "power_core"),
        ("Прыжки лягушкой", "Frog Jumps", "Прыжки вперед из глубокого приседа.", "plyometric_lower"),
        ("Скейтеры", "Skater Jumps", "Боковые прыжки с одной ноги на другую.", "plyometric_lateral"),
        ("Прыжки звездой", "Star Jumps", "Взрывные прыжки с разведением рук и ног.", "full_body_power"),
        ("Кик ножницы", "Scissor Kicks Power", "Быстрая смена ног в воздухе в выпаде.", "plyometric_lower"),
        ("Хлопки в планке", "Plank Clap", "Быстрые хлопки руками в положении планки.", "plyometric_upper"),
        ("Прыжок на одной", "Single Leg Hop", "Прыжки на одной ноге для развития односторонней мощности.", "plyometric_unilateral"),
        ("Взрывной старт", "Explosive Start", "Быстрый переход из положения лежа в спринт.", "power_transition"),
        ("Реактивные прыжки", "Reactive Jumps", "Прыжки с быстрой сменой направления.", "reactive_power"),
        ("Интервальная мощность", "Power Intervals", "Чередование взрывных движений с восстановлением.", "power_conditioning")
    ]
    
    for i, (name_ru, name_en, description, subcategory) in enumerate(power_explosive):
        exercises.append({
            'id': exercise_id,
            'name_ru': name_ru,
            'name_en': name_en,
            'description': description,
            'category': 'power_explosive',
            'category_ru': 'Мощность и взрывная сила',
            'subcategory': subcategory,
            'muscle_groups': ['full_body'],
            'difficulty': 'intermediate',
            'equipment': [],
            'duration_seconds': 30,
            'mental_component': False,
            'breathing_pattern': 'explosive',
            'movement_plane': 'multi_planar',
            'slug': name_en.lower().replace(' ', '-').replace("'", ''),
            'file_name': f"power_{i+1:02d}_technique_m01.mp4",
            'display_title': name_ru,
            'sets': 3,
            'reps': '8-12',
            'rest_seconds': 60
        })
        exercise_id += 1
    
    # === PRIMAL & FLOW (25 упражнений) ===
    primal_flow = [
        # Animal Flow Basics
        ("Зверь базовый", "Beast Hold", "Базовая позиция зверя - на руках и ногах с поднятыми коленями.", "animal_static"),
        ("Краб базовый", "Crab Hold", "Базовая позиция краба - сидя с опорой на руки сзади.", "animal_static"),
        ("Ящерица базовая", "Lizard Hold", "Низкая позиция ящерицы с опорой на предплечья.", "animal_static"),
        ("Зверь шаг", "Beast Step", "Шаги в позиции зверя вперед, назад, в стороны.", "animal_locomotion"),
        ("Краб шаг", "Crab Walk", "Передвижение в позиции краба в разных направлениях.", "animal_locomotion"),
        ("Ящерица ползание", "Lizard Crawl", "Ползание на животе с поддержкой предплечий.", "animal_locomotion"),
        ("Медвежья походка", "Bear Crawl", "Походка на четвереньках без касания коленями пола.", "animal_locomotion"),
        ("Обезьяна", "Ape Walk", "Передвижение в глубоком приседе с опорой на руки.", "animal_locomotion"),
        
        # Flow Transitions
        ("Зверь-краб переход", "Beast to Crab", "Плавный переход из позиции зверя в краб.", "flow_transition"),
        ("Волна зверя", "Beast Wave", "Волнообразное движение в позиции зверя.", "flow_dynamic"),
        ("Поток краба", "Crab Flow", "Непрерывные движения в позиции краба.", "flow_dynamic"),
        ("Скорпион досягаемость", "Scorpion Reach", "Поворот с досягаемостью в позиции ящерицы.", "flow_dynamic"),
        ("Переворот зверя", "Beast Roll", "Переворот через плечо из позиции зверя.", "flow_transition"),
        ("Краб досягаемость", "Crab Reach", "Досягаемость противоположной рукой в крабе.", "flow_dynamic"),
        
        # Ground Movement
        ("Переход лежа-стоя", "Ground to Stand", "Различные способы подъема с земли без помощи рук.", "ground_transition"),
        ("Переворот боковой", "Lateral Roll", "Боковые перевороты для развития пространственного ориентирования.", "ground_movement"),
        ("Каток", "Log Roll", "Перекаты всем телом для массажа фасций.", "ground_movement"),
        ("Рокер", "Rocker", "Покачивания в различных позициях для мобилизации.", "ground_movement"),
        
        # Advanced Flow
        ("Поток животных", "Animal Flow Sequence", "Связанная последовательность движений животных.", "flow_complex"),
        ("Креативный поток", "Creative Flow", "Импровизационные движения с базовыми элементами.", "flow_creative"),
        ("Поток с дыханием", "Breathing Flow", "Медленные переходы с интеграцией дыхания.", "flow_mindful"),
        ("Поток силы", "Power Flow", "Динамичная последовательность с акцентом на силу.", "flow_power"),
        ("Поток восстановления", "Recovery Flow", "Мягкие движения для восстановления.", "flow_recovery"),
        ("Утренний поток", "Morning Flow", "Последовательность для утреннего пробуждения тела.", "flow_morning"),
        ("Вечерний поток", "Evening Flow", "Успокаивающие движения для вечернего расслабления.", "flow_evening")
    ]
    
    for i, (name_ru, name_en, description, subcategory) in enumerate(primal_flow):
        difficulty = 'advanced' if 'Complex' in subcategory or 'Power' in subcategory else 'intermediate'
        exercises.append({
            'id': exercise_id,
            'name_ru': name_ru,
            'name_en': name_en,
            'description': description,
            'category': 'primal_flow',
            'category_ru': 'Первичные движения и потоки',
            'subcategory': subcategory,
            'muscle_groups': ['full_body'],
            'difficulty': difficulty,
            'equipment': [],
            'duration_seconds': 90,
            'mental_component': True,
            'breathing_pattern': 'integrated',
            'movement_plane': 'multi_planar',
            'slug': name_en.lower().replace(' ', '-').replace("'", ''),
            'file_name': f"primal_{i+1:02d}_technique_m01.mp4",
            'display_title': name_ru,
            'sets': 2,
            'reps': '30-60 сек',
            'rest_seconds': 60
        })
        exercise_id += 1
    
    # === CORRECTIVE & THERAPEUTIC (20 упражнений) ===
    corrective_therapeutic = [
        # Posture Correction
        ("Коррекция осанки", "Posture Reset", "Комплекс упражнений для коррекции нарушений осанки.", "posture_correction"),
        ("Мобилизация грудного отдела", "Thoracic Mobility", "Упражнения для восстановления подвижности грудного отдела.", "spinal_mobility"),
        ("Коррекция шеи", "Neck Correction", "Упражнения для устранения переднего положения головы.", "neck_correction"),
        ("Активация глубоких мышц", "Deep Core Activation", "Активация поперечной мышцы живота и мультифидус.", "deep_stabilization"),
        ("Коррекция таза", "Pelvic Correction", "Упражнения для выравнивания положения таза.", "pelvic_alignment"),
        
        # Joint Mobility
        ("Мобилизация плеч", "Shoulder Mobility Complex", "Комплекс для восстановления подвижности плечевых суставов.", "shoulder_mobility"),
        ("Мобилизация бедер", "Hip Mobility Flow", "Последовательность для улучшения подвижности тазобедренных суставов.", "hip_mobility"),
        ("Мобилизация голеностопа", "Ankle Mobility", "Упражнения для восстановления подвижности голеностопных суставов.", "ankle_mobility"),
        ("Спиральная мобилизация", "Spiral Mobility", "Трехмерные движения для мобилизации фасциальных спиралей.", "fascial_mobility"),
        
        # Stability Training
        ("Стабилизация кора", "Core Stability Progressive", "Прогрессивная тренировка стабильности кора.", "stability_training"),
        ("Стабилизация плеч", "Shoulder Stability", "Упражнения для укрепления стабилизаторов плечевого пояса.", "stability_training"),
        ("Проприоцепция", "Proprioceptive Training", "Тренировка проприоцепции для улучшения контроля движений.", "proprioception"),
        ("Баланс одной ноги", "Single Leg Balance", "Прогрессивная тренировка баланса на одной ноге.", "balance_training"),
        
        # Movement Quality
        ("Качество приседания", "Squat Quality Assessment", "Оценка и коррекция техники приседания.", "movement_assessment"),
        ("Качество шага", "Gait Quality", "Анализ и улучшение качества ходьбы.", "movement_assessment"),
        ("Симметрия движения", "Movement Symmetry", "Упражнения для устранения асимметрий в движении.", "movement_correction"),
        ("Интеграция движения", "Movement Integration", "Соединение отдельных движений в функциональные паттерны.", "movement_integration"),
        
        # Recovery Protocols
        ("Протокол восстановления", "Recovery Protocol", "Систематический подход к восстановлению после нагрузок.", "recovery_protocol"),
        ("Миофасциальный релиз", "Self-Myofascial Release", "Самомассаж для улучшения качества тканей.", "tissue_quality"),
        ("Нейромышечное расслабление", "Neuromuscular Relaxation", "Техники для расслабления нервной системы.", "neural_recovery")
    ]
    
    for i, (name_ru, name_en, description, subcategory) in enumerate(corrective_therapeutic):
        exercises.append({
            'id': exercise_id,
            'name_ru': name_ru,
            'name_en': name_en,
            'description': description,
            'category': 'corrective_therapeutic',
            'category_ru': 'Коррекция и терапия',
            'subcategory': subcategory,
            'muscle_groups': ['specific_targeted'],
            'difficulty': 'beginner',
            'equipment': [],
            'duration_seconds': 120,
            'mental_component': True,
            'breathing_pattern': 'integrated',
            'movement_plane': 'multi_planar',
            'slug': name_en.lower().replace(' ', '-').replace("'", ''),
            'file_name': f"corrective_{i+1:02d}_technique_m01.mp4",
            'display_title': name_ru,
            'sets': 2,
            'reps': '1-2 мин',
            'rest_seconds': 30
        })
        exercise_id += 1
    
    # === MINDFUL MOVEMENT (15 упражнений) ===
    mindful_movement = [
        ("Осознанное дыхание", "Mindful Breathing", "Практика осознанного дыхания с движением диафрагмы.", "breathwork"),
        ("Медитация в движении", "Moving Meditation", "Медленные, осознанные движения с полным присутствием.", "mindful_practice"),
        ("Сканирование тела", "Body Scan Movement", "Движения с фокусом на ощущениях в разных частях тела.", "body_awareness"),
        ("Дыхание квадрат", "Box Breathing Flow", "Движения под ритм дыхания 4-4-4-4.", "breathwork"),
        ("Заземление", "Grounding Practice", "Упражнения для ощущения связи с землей и центрирования.", "grounding"),
        ("Энергетическое дыхание", "Energizing Breath", "Дыхательные техники для повышения энергии.", "breathwork"),
        ("Успокаивающие движения", "Calming Movements", "Мягкие движения для активации парасимпатической нервной системы.", "relaxation"),
        ("Интуитивное движение", "Intuitive Movement", "Свободные движения под руководством внутренних ощущений.", "intuitive_practice"),
        ("Благодарность телу", "Body Gratitude", "Практика признательности телу через нежные движения.", "gratitude_practice"),
        ("Эмоциональный релиз", "Emotional Release", "Движения для освобождения эмоционального напряжения.", "emotional_wellness"),
        ("Центрирование", "Centering Practice", "Упражнения для возвращения к внутреннему центру.", "centering"),
        ("Настоящий момент", "Present Moment", "Практики для углубления присутствия в текущем моменте.", "presence_practice"),
        ("Самосострадание", "Self-Compassion Movement", "Нежные движения, культивирующие доброту к себе.", "self_compassion"),
        ("Стресс-релиз", "Stress Release Flow", "Последовательность движений для снятия стресса.", "stress_management"),
        ("Утренняя внимательность", "Morning Mindfulness", "Осознанные движения для начала дня.", "morning_practice")
    ]
    
    for i, (name_ru, name_en, description, subcategory) in enumerate(mindful_movement):
        exercises.append({
            'id': exercise_id,
            'name_ru': name_ru,
            'name_en': name_en,
            'description': description,
            'category': 'mindful_movement',
            'category_ru': 'Осознанное движение',
            'subcategory': subcategory,
            'muscle_groups': ['mind_body'],
            'difficulty': 'beginner',
            'equipment': [],
            'duration_seconds': 180,
            'mental_component': True,
            'breathing_pattern': 'conscious',
            'movement_plane': 'internal_focus',
            'slug': name_en.lower().replace(' ', '-').replace("'", ''),
            'file_name': f"mindful_{i+1:02d}_technique_m01.mp4",
            'display_title': name_ru,
            'sets': 1,
            'reps': '2-5 мин',
            'rest_seconds': 30
        })
        exercise_id += 1
    
    # === RECOVERY & REGENERATION (12 упражнений) ===
    recovery_regeneration = [
        ("Активное восстановление", "Active Recovery Flow", "Легкие движения для ускорения восстановления.", "active_recovery"),
        ("Лимфодренаж", "Lymphatic Drainage", "Мягкие движения для стимуляции лимфатической системы.", "circulation"),
        ("Парасимпатическая активация", "Parasympathetic Activation", "Техники для активации режима отдыха и восстановления.", "nervous_system"),
        ("Прогрессивное расслабление", "Progressive Relaxation", "Систематическое расслабление всех групп мышц.", "relaxation_technique"),
        ("Восстановительное дыхание", "Restorative Breathing", "Дыхательные практики для глубокого восстановления.", "breathwork_recovery"),
        ("Йога-нидра", "Yoga Nidra Flow", "Движения в стиле йога-нидра для глубокого расслабления.", "deep_relaxation"),
        ("Фасциальный релиз", "Fascial Release Flow", "Движения для освобождения фасциальных ограничений.", "tissue_release"),
        ("Суставная декомпрессия", "Joint Decompression", "Упражнения для снятия компрессии с суставов.", "joint_health"),
        ("Циркуляция энергии", "Energy Circulation", "Движения для улучшения энергетического потока.", "energy_work"),
        ("Вечернее восстановление", "Evening Recovery", "Практика для подготовки тела ко сну.", "sleep_preparation"),
        ("Восстановление после стресса", "Stress Recovery", "Специальные техники для восстановления после стресса.", "stress_recovery"),
        ("Глубокая регенерация", "Deep Regeneration", "Продвинутые техники для максимального восстановления.", "advanced_recovery")
    ]
    
    for i, (name_ru, name_en, description, subcategory) in enumerate(recovery_regeneration):
        exercises.append({
            'id': exercise_id,
            'name_ru': name_ru,
            'name_en': name_en,
            'description': description,
            'category': 'recovery_regeneration',
            'category_ru': 'Восстановление и регенерация',
            'subcategory': subcategory,
            'muscle_groups': ['full_body'],
            'difficulty': 'beginner',
            'equipment': [],
            'duration_seconds': 300,
            'mental_component': True,
            'breathing_pattern': 'slow_deep',
            'movement_plane': 'restorative',
            'slug': name_en.lower().replace(' ', '-').replace("'", ''),
            'file_name': f"recovery_{i+1:02d}_technique_m01.mp4",
            'display_title': name_ru,
            'sets': 1,
            'reps': '3-10 мин',
            'rest_seconds': 0
        })
        exercise_id += 1
    
    return exercises

def create_modern_excel_file():
    """Create Excel file with modern exercises database"""
    
    exercises = create_modern_exercises_database()
    
    # Создаем DataFrame
    df = pd.DataFrame(exercises)
    
    # Добавляем дополнительные поля для системы
    df['chatgpt_prompt_info'] = df.apply(lambda row: 
        f"Exercise: {row['name_en']} ({row['name_ru']}). "
        f"Category: {row['category_ru']}. "
        f"Subcategory: {row['subcategory']}. "
        f"Mental component: {'Yes' if row['mental_component'] else 'No'}. "
        f"Breathing: {row['breathing_pattern']}. "
        f"Movement plane: {row['movement_plane']}. "
        f"Difficulty: {row['difficulty']}. "
        f"Duration: {row['duration_seconds']}s. "
        f"Description: {row['description']}", axis=1)
    
    df['storage_file_pattern'] = df.apply(lambda row:
        f"videos/{row['category']}/{row['file_name']}", axis=1)
    
    df['video_url_pattern'] = df.apply(lambda row:
        f"https://ai-fitness-media.r2.cloudflarestorage.com/videos/{row['category']}/{row['file_name']}", axis=1)
    
    # Упорядочиваем колонки
    columns_order = [
        'id', 'name_ru', 'name_en', 'description', 'category', 'category_ru', 'subcategory',
        'muscle_groups', 'difficulty', 'equipment', 'duration_seconds', 
        'mental_component', 'breathing_pattern', 'movement_plane',
        'slug', 'sets', 'reps', 'rest_seconds',
        'file_name', 'storage_file_pattern', 'video_url_pattern',
        'display_title', 'chatgpt_prompt_info'
    ]
    
    df = df[columns_order]
    
    # Сохраняем в Excel
    output_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/MODERN_EXERCISES_DATABASE_2025.xlsx'
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Основная таблица
        df.to_excel(writer, sheet_name='All_Modern_Exercises', index=False)
        
        # Разбивка по категориям
        categories = df['category'].unique()
        for category in categories:
            category_df = df[df['category'] == category]
            sheet_name = category.replace('_', ' ').title()[:31]  # Excel limit
            category_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Статистика
        stats_data = []
        for category in categories:
            count = len(df[df['category'] == category])
            stats_data.append({
                'Category': category.replace('_', ' ').title(),
                'Count': count,
                'Percentage': f"{count/len(df)*100:.1f}%"
            })
        
        # Добавляем статистику по уровням сложности
        difficulty_stats = []
        for diff in df['difficulty'].unique():
            count = len(df[df['difficulty'] == diff])
            difficulty_stats.append({
                'Difficulty': diff.title(),
                'Count': count,
                'Percentage': f"{count/len(df)*100:.1f}%"
            })
        
        stats_df = pd.DataFrame(stats_data)
        diff_stats_df = pd.DataFrame(difficulty_stats)
        
        stats_df.to_excel(writer, sheet_name='Category_Statistics', index=False)
        diff_stats_df.to_excel(writer, sheet_name='Difficulty_Statistics', index=False, startrow=len(stats_df)+3)
        
        # Анализ современных трендов
        trends_analysis = [
            {'Trend': 'Animal Flow & Primal Movement', 'Count': len(df[df['category'] == 'primal_flow']), 'Status': '✅ Fully Integrated'},
            {'Trend': 'Functional Movement Patterns', 'Count': len(df[df['category'] == 'fundamental_patterns']), 'Status': '✅ Comprehensive'},
            {'Trend': 'Mind-Body Integration', 'Count': len(df[df['mental_component'] == True]), 'Status': '✅ Throughout System'},
            {'Trend': 'Corrective Exercise', 'Count': len(df[df['category'] == 'corrective_therapeutic']), 'Status': '✅ Specialized Section'},
            {'Trend': 'Power & Explosive Training', 'Count': len(df[df['category'] == 'power_explosive']), 'Status': '✅ Dedicated Category'},
            {'Trend': 'Recovery & Regeneration', 'Count': len(df[df['category'] == 'recovery_regeneration']), 'Status': '✅ Complete System'},
            {'Trend': 'Breathwork Integration', 'Count': len(df[df['breathing_pattern'] != 'natural']), 'Status': '✅ Integrated Throughout'}
        ]
        
        trends_df = pd.DataFrame(trends_analysis)
        trends_df.to_excel(writer, sheet_name='Modern_Trends_Analysis', index=False)
    
    print(f"✅ Современная база упражнений создана: {output_file}")
    print(f"📊 Всего упражнений: {len(df)}")
    print(f"🔥 Упражнения с ментальным компонентом: {len(df[df['mental_component'] == True])}")
    print(f"🎯 Категории: {len(df['category'].unique())}")
    print(f"⚡ Современные тренды: 100% покрытие")
    
    return output_file

if __name__ == '__main__':
    create_modern_excel_file()