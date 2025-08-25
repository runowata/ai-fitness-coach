"""Упрощенные Pydantic схемы для валидации GPT-5 ответов"""

from typing import List
from pydantic import BaseModel, Field, field_validator
import re


class WorkoutDay(BaseModel):
    """Один день тренировок - только коды упражнений"""
    day_number: int = Field(..., ge=1, le=7, description="Номер дня недели (1-7)")
    is_rest_day: bool = Field(False, description="День отдыха")
    
    # Массивы кодов упражнений по категориям
    warmup_exercises: List[str] = Field(default_factory=list, description="Коды разминки (WZ001-WZ021)")
    main_exercises: List[str] = Field(default_factory=list, description="Коды основных упражнений (EX001-EX063)")  
    endurance_exercises: List[str] = Field(default_factory=list, description="Коды выносливости (SX001-SX021)")
    cooldown_exercises: List[str] = Field(default_factory=list, description="Коды растяжки (CZ001-CZ021)")
    
    @field_validator('warmup_exercises')
    @classmethod
    def validate_warmup_codes(cls, v):
        """Проверяем коды разминки"""
        for code in v:
            if not re.match(r'^WZ\d{3}(_v\d+)?$', code):
                raise ValueError(f"Неверный код разминки: {code}. Ожидается формат WZ001, WZ015_v2")
        return v
    
    @field_validator('main_exercises')
    @classmethod
    def validate_main_codes(cls, v):
        """Проверяем коды основных упражнений"""
        for code in v:
            if not re.match(r'^EX\d{3}(_v\d+)?$', code):
                raise ValueError(f"Неверный код основного упражнения: {code}. Ожидается формат EX027, EX001_v2")
        return v
    
    @field_validator('endurance_exercises')
    @classmethod
    def validate_endurance_codes(cls, v):
        """Проверяем коды упражнений на выносливость"""
        for code in v:
            if not re.match(r'^SX\d{3}(_v\d+)?$', code):
                raise ValueError(f"Неверный код упражнения на выносливость: {code}. Ожидается формат SX001, SX005_v2")
        return v
    
    @field_validator('cooldown_exercises') 
    @classmethod
    def validate_cooldown_codes(cls, v):
        """Проверяем коды растяжки"""
        for code in v:
            if not re.match(r'^CZ\d{3}(_v\d+)?$', code):
                raise ValueError(f"Неверный код растяжки: {code}. Ожидается формат CZ001, CZ010_v2")
        return v


class WorkoutWeek(BaseModel):
    """Неделя тренировок"""
    week_number: int = Field(..., ge=1, le=8, description="Номер недели")
    days: List[WorkoutDay] = Field(..., min_length=7, max_length=7, description="7 дней недели")
    
    @field_validator('days')
    @classmethod
    def validate_days(cls, v):
        """Проверяем что есть ровно 7 дней с номерами 1-7"""
        if len(v) != 7:
            raise ValueError("В каждой неделе должно быть ровно 7 дней")
        
        day_numbers = [day.day_number for day in v]
        expected_days = list(range(1, 8))
        
        if sorted(day_numbers) != expected_days:
            raise ValueError("Дни должны быть пронумерованы 1-7 без пропусков")
        
        return v


class SimpleWorkoutPlan(BaseModel):
    """Упрощенный план тренировок - только коды упражнений"""
    plan_name: str = Field(..., min_length=10, max_length=100, description="Название плана")
    duration_weeks: int = Field(..., ge=2, le=8, description="Длительность в неделях")
    goal: str = Field(..., min_length=20, max_length=200, description="Цель плана")
    weeks: List[WorkoutWeek] = Field(..., description="Недели тренировок")
    
    @field_validator('weeks')
    @classmethod
    def validate_weeks(cls, v, info):
        """Проверяем соответствие количества недель"""
        duration_weeks = info.data.get('duration_weeks')
        if duration_weeks and len(v) != duration_weeks:
            raise ValueError(f"Ожидается {duration_weeks} недель, получено {len(v)}")
        
        # Проверяем последовательность номеров недель
        week_numbers = [week.week_number for week in v]
        expected_weeks = list(range(1, len(v) + 1))
        
        if sorted(week_numbers) != expected_weeks:
            raise ValueError("Недели должны быть пронумерованы последовательно начиная с 1")
        
        return v


def validate_simple_ai_plan(raw_response: str) -> SimpleWorkoutPlan:
    """
    Валидация упрощенного ответа GPT-5
    
    Args:
        raw_response: JSON строка от AI
        
    Returns:
        Валидированный SimpleWorkoutPlan
        
    Raises:
        ValueError: При ошибках валидации
    """
    import json
    
    # Парсим JSON
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Неверный JSON от AI: {str(e)}")
    
    # Валидируем Pydantic схемой
    try:
        plan = SimpleWorkoutPlan.model_validate(data)
    except Exception as e:
        raise ValueError(f"Ошибка валидации плана: {str(e)}")
    
    return plan