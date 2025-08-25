# Создание научно-обоснованного плана тренировок

## Данные клиента:
- **Возраст**: {{age}} лет | **Рост/вес**: {{height}}см, {{weight}}кг
- **Цель**: {{primary_goal}}
- **Ограничения**: {{injuries}}  
- **Оборудование**: {{equipment_list}}
- **Длительность**: {{duration_weeks}} недель

## Детальная анкета:
```json
{{onboarding_payload_json}}
```

## Задача Science-Based Coach:

Создайте **evidence-based план** на {{duration_weeks}} недель с учетом:

### 🧠 Психо-социальные факторы:
- Мотивационный профиль и барьеры
- Стратегии adherence для данного lifestyle
- Оптимальная частота под жизненный ритм

### 🔬 Биомеханическая оценка:
- Вероятные дисбалансы (возраст + образ жизни + травмы)
- Приоритеты коррекции движений
- Прогрессивная адаптация нагрузок

### 📊 Структурированная периодизация:
- **Подготовка** (1-2 недели): Movement quality, tissue adaptation
- **Накопление** (3-4 недели): Volume progression, strength endurance
- **Интенсификация** (5-6 недели): Load progression, power development

### 🛡️ Injury Prevention:
- Специфические risk factors клиента  
- Corrective exercises под выявленные проблемы
- Progressive loading для безопасности

## Технические требования:

**ЕЖЕДНЕВНАЯ ПРОГРАММА** - 7 дней, каждый содержит **ТОЛЬКО КОДЫ**:

- **warmup_exercises**: 2 кода мобилизации (WZ001-WZ021)
- **main_exercises**: 3-5 кодов основной работы (EX001-EX063)  
- **endurance_exercises**: 1-2 кода кондиции (SX001-SX021)
- **cooldown_exercises**: 2 кода восстановления (CZ001-CZ021)

### Принципы подбора:
1. **Прогрессивность** от недели к неделе
2. **Специфичность** под цели и ограничения
3. **Вариативность** для предотвращения адаптации  
4. **Безопасность** с учетом травм
5. **Реалистичность** под уровень подготовки

### Примеры для lower back pain:
- Warmup: deep core activation, hip mobility
- Main: hip-hinge patterns, posterior chain, anti-extension core  
- Endurance: low-impact cardio без spine compression
- Cooldown: hip flexor stretch, lumbar relaxation

**КРИТИЧЕСКИ ВАЖНО:**
- Используйте ТОЛЬКО коды из whitelist
- НЕ указывайте подходы/повторы - только коды
- Полный план {{duration_weeks}} × 7 = дней
- Все 4 категории каждый день

Результат: клиент получит **comprehensive educational experience** с пониманием принципов тренировки.