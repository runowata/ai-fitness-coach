# Техническое задание: High-Performance Training Program

## Параметры клиента:
- **Возраст**: {{age}} лет | **Габариты**: {{height}} см / {{weight}} кг
- **Цель**: {{primary_goal}}
- **Ограничения**: {{injuries}}
- **Арсенал**: {{equipment_list}}
- **Дедлайн**: {{duration_weeks}} недель

## Данные клиента:
```json
{{onboarding_payload_json}}
```

## Техническое задание для Pro Coach:

Разработайте **максимально эффективную программу** на {{duration_weeks}} недель для достижения конкретных, измеримых результатов.

### ⚡ Performance Requirements:

1. **Time Efficiency**: Максимум результата за минимум времени
2. **Measurable Outcomes**: Четкие KPI для каждой недели
3. **Progressive Overload**: Систематическое увеличение сложности
4. **Compound Focus**: Приоритет многосуставным упражнениям
5. **Periodization**: Научно обоснованные тренировочные циклы

### 📊 Структура программы:

#### 🎯 Phase 1: Foundation (Week 1-2)
- **Objective**: Movement preparation, техническая база
- **Intensity**: 65-75% от максимальной нагрузки
- **Volume**: Установление тренировочного ритма
- **Focus**: Нейромышечная адаптация, injury prevention

#### 🏃 Phase 2: Accumulation (Week 3-4)  
- **Objective**: Volume progression, work capacity
- **Intensity**: 70-80% от максимальной нагрузки
- **Volume**: Увеличение на 15-20% от предыдущей фазы
- **Focus**: Метаболические адаптации, strength endurance

#### 🔥 Phase 3: Intensification (Week 5-6)
- **Objective**: Peak performance, strength/power development
- **Intensity**: 80-90% от максимальной нагрузки  
- **Volume**: Снижение объема, повышение интенсивности
- **Focus**: Нейромышечная мощность, peak adaptations

### 💪 Training Methodology:

#### Daily Structure Requirements:
- **Activation Phase**: 2 упражнения neural activation (WZ001-WZ021)
- **Main Work**: 3-5 упражнений compound movements (EX001-EX063)
- **Conditioning**: 1-2 упражнения metabolic work (SX001-SX021)
- **Recovery**: 2 упражнения regeneration (CZ001-CZ021)

#### Performance Standards:
- **Week 1-2**: Establish baselines, perfect technique
- **Week 3-4**: 10-15% increase in working loads
- **Week 5-6**: Peak performance, 20-25% improvement from baseline

### 🎯 Goal-Specific Programming:

**Fat Loss Protocol:**
- High-intensity intervals, metabolic circuits
- Compound movements with minimal rest
- Cardio-strength combinations

**Muscle Building Protocol:**
- Progressive overload focus
- Volume accumulation strategies  
- Time under tension optimization

**Athletic Performance Protocol:**
- Power development emphasis
- Movement quality refinement
- Sport-specific adaptations

### 📈 Expected Outcomes by Week:

**Week 1-2**: Movement mastery, routine establishment
**Week 3-4**: Visible strength/endurance improvements  
**Week 5-6**: Significant performance gains, body composition changes

## Выходной формат:

**ЕЖЕДНЕВНЫЕ ТРЕНИРОВКИ** - строгая структура 7 дней в неделю.

### JSON Requirements:
Верните валидный JSON с **ТОЛЬКО КОДАМИ УПРАЖНЕНИЙ**:

```json
{
  "plan_name": "Descriptive name",
  "duration_weeks": {{duration_weeks}},
  "goal": "performance_goal",
  "weeks": [
    {
      "week_number": 1,
      "phase": "Foundation/Accumulation/Intensification", 
      "days": [
        {
          "day_number": 1,
          "warmup_exercises": ["WZ001", "WZ002"],
          "main_exercises": ["EX001", "EX005", "EX010", "EX015"],
          "endurance_exercises": ["SX001", "SX005"], 
          "cooldown_exercises": ["CZ001", "CZ002"]
        }
        // ... complete 7 days
      ]
    }
    // ... complete {{duration_weeks}} weeks
  ]
}
```

### 🔧 Technical Specifications:
- **Full Duration**: {{duration_weeks}} полных недель ({{duration_weeks}} × 7 дней)
- **Consistent Structure**: Каждый день содержит все 4 категории  
- **Progressive Difficulty**: Усложнение от недели к неделе
- **Equipment Match**: Соответствие доступному оборудованию
- **Injury Considerations**: Учет медицинских ограничений

### ⚠️ Critical Requirements:
- Используйте ТОЛЬКО коды из предоставленного whitelist
- НЕ указывайте подходы/повторы/веса - только коды
- НЕ создавайте новые коды упражнений
- Обеспечьте полную программу без пропусков дней

### 🎬 System Integration:
Автоматически создаются:
- Технические видео для каждого упражнения
- Performance tracking metrics  
- Progressive load recommendations
- Form correction cues

**Результат**: Клиент получает **systematic performance program** с четкой структурой, измеримыми целями и гарантированным прогрессом за {{duration_weeks}} недель.