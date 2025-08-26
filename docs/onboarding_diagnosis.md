# Диагностика системы онбординга

## 📊 Структура моделей

### 1. OnboardingQuestion
- ✅ **Есть**: ai_field_name - ключ для передачи в AI
- ✅ **Типы вопросов**: single_choice, multiple_choice, number, text, scale, body_map
- ✅ **Порядок**: order + block_order для группировки

### 2. UserOnboardingResponse  
- ✅ **Связи**: user + question (unique_together)
- ✅ **Гибкое хранение**: answer_text, answer_options (M2M), answer_number, answer_scale, answer_body_map
- ✅ **Метод**: get_answer_value() - универсальное извлечение значения

### 3. OnboardingSession
- ❌ **НЕ используется** в OnboardingDataProcessor
- Есть модель, но нет связи с UserOnboardingResponse

### 4. UserProfile
- ✅ **Богатая структура**: health_conditions, chronic_pain_areas, sexual_health_goals и т.д. 
- ✅ **Архетип**: mentor/professional/peer
- ❌ **НЕТ полей**: biological_sex, fitness_level, equipment_list (используются заглушки)

## 🔍 Проблемы OnboardingDataProcessor

### Текущая реализация:
```python
# ЗАГЛУШКИ вместо реальных данных:
'biological_sex': getattr(profile, 'biological_sex', 'male'),  # НЕТ в UserProfile
'fitness_level': getattr(profile, 'fitness_level', 'beginner'),  # НЕТ в UserProfile  
'equipment_list': OnboardingDataProcessor._format_equipment(profile),  # НЕТ available_equipment
'injuries': getattr(profile, 'injuries', 'none'),  # НЕТ, есть injuries_surgeries
```

### Реальные данные игнорируются:
- ❌ UserOnboardingResponse вообще не читается
- ❌ ai_field_name из OnboardingQuestion не используется
- ❌ Все богатство UserProfile (health_conditions, chronic_pain_areas и т.д.) не передается в AI

## ✅ Что нужно исправить

### 1. Правильный сбор данных из онбординга:
```python
def collect_user_data(user):
    # 1) Читаем UserOnboardingResponse
    responses = UserOnboardingResponse.objects.filter(user=user).select_related('question')
    
    # 2) Маппим по ai_field_name
    context = {}
    for resp in responses:
        key = resp.question.ai_field_name
        value = resp.get_answer_value()
        context[key] = value
    
    # 3) Дополняем из UserProfile реальными полями
    profile = user.profile
    context.update({
        'age': profile.age,
        'height': profile.height,
        'weight': profile.weight,
        'archetype': profile.archetype,
        'health_conditions': profile.health_conditions,
        'chronic_pain_areas': profile.chronic_pain_areas,
        'injuries_surgeries': profile.injuries_surgeries,
        'sexual_health_goals': profile.sexual_health_goals,
        # и т.д. - все реальные поля
    })
    
    return context
```

### 2. Убрать фиктивные поля:
- biological_sex → удалить (нет в модели)
- fitness_level → удалить (нет в модели)  
- equipment_list → удалить (нет в модели)
- injuries → заменить на injuries_surgeries (реальное поле)

### 3. Использовать OnboardingSession (опционально):
- Можно фильтровать по последней завершенной сессии
- Но сейчас нет связи Session ↔ Response

## 🎯 План действий

1. **Исправить OnboardingDataProcessor.collect_user_data()**
   - Читать UserOnboardingResponse 
   - Использовать ai_field_name
   - Брать реальные поля из UserProfile

2. **Убрать заглушки и фиктивные поля**

3. **Протестировать полный flow**:
   - Пользователь заполняет анкету → UserOnboardingResponse
   - collect_user_data() собирает все ответы
   - AI получает реальный контекст
   - План генерируется на основе реальных данных

## 📝 Выводы

**✅ Инфраструктура есть и хорошая:**
- Модели правильно спроектированы
- ai_field_name готов для маппинга  
- get_answer_value() универсален

**❌ Но не используется:**
- OnboardingDataProcessor игнорирует UserOnboardingResponse
- Вместо реальных данных - заглушки
- Богатство UserProfile не передается в AI

**Рекомендация:** Не нужно создавать новые модели или поля. Нужно правильно использовать существующие!