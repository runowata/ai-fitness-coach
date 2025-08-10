"""Pydantic schemas for strict AI response validation"""

from pydantic import BaseModel, Field, ValidationError, ConfigDict, field_validator
from typing import List, Optional, Dict, Any
import re


class ExerciseItem(BaseModel):
    """Single exercise in a workout day"""
    exercise_slug: str = Field(..., description="Exercise slug or ID")
    sets: Optional[int] = Field(None, ge=1, le=10, description="Number of sets")
    reps: Optional[str] = Field(None, description="Reps (can be number or range like '10-12')")
    rest_seconds: Optional[int] = Field(None, ge=10, le=600, description="Rest time in seconds")
    duration_seconds: Optional[int] = Field(None, ge=10, le=1800, description="Exercise duration")
    
    @field_validator('exercise_slug')
    @classmethod
    def validate_exercise_slug(cls, v):
        """Validate exercise slug format"""
        if not v or not isinstance(v, str):
            raise ValueError("exercise_slug must be a non-empty string")
        # Allow both formats: 'push-ups' and 'EX001'
        if not (v.replace('-', '').replace('_', '').isalnum()):
            raise ValueError("exercise_slug contains invalid characters")
        return v.lower()


class WorkoutDay(BaseModel):
    """Single day in a workout plan"""
    day_number: int = Field(..., ge=1, le=7, description="Day number (1-7)")
    workout_name: str = Field(..., min_length=3, max_length=200, description="Workout name")
    is_rest_day: bool = Field(False, description="Is this a rest day")
    exercises: List[ExerciseItem] = Field(default_factory=list, description="List of exercises")
    confidence_task: Optional[str] = Field(None, max_length=500, description="Daily confidence task")
    
    @field_validator('exercises')
    @classmethod
    def validate_exercises(cls, v, info):
        """Validate exercises based on rest day status"""
        is_rest = info.data.get('is_rest_day', False)
        if is_rest and len(v) > 0:
            raise ValueError("Rest days should not have exercises")
        if not is_rest and len(v) == 0:
            raise ValueError("Non-rest days must have at least one exercise")
        return v


class WorkoutWeek(BaseModel):
    """Single week in a workout plan"""
    week_number: int = Field(..., ge=1, le=12, description="Week number")
    week_focus: Optional[str] = Field(None, max_length=200, description="Week focus/theme")
    days: List[WorkoutDay] = Field(..., min_length=7, max_length=7, description="7 days in a week")
    
    @field_validator('days')
    @classmethod  
    def validate_days(cls, v):
        """Validate that we have exactly 7 days numbered 1-7"""
        if len(v) != 7:
            raise ValueError("Each week must have exactly 7 days")
        
        day_numbers = [day.day_number for day in v]
        expected_days = list(range(1, 8))
        
        if sorted(day_numbers) != expected_days:
            raise ValueError("Days must be numbered 1-7 with no duplicates")
        
        return v


class WorkoutPlan(BaseModel):
    """Complete workout plan from AI"""
    model_config = ConfigDict(extra="forbid")  # No extra fields allowed
    
    plan_name: str = Field(..., min_length=5, max_length=200, description="Plan name")
    duration_weeks: int = Field(..., ge=4, le=12, description="Plan duration in weeks")
    goal: str = Field(..., min_length=10, max_length=300, description="Plan goal")
    weeks: List[WorkoutWeek] = Field(..., description="List of workout weeks")
    
    @field_validator('weeks')
    @classmethod
    def validate_weeks(cls, v, info):
        """Validate weeks match duration_weeks"""
        duration_weeks = info.data.get('duration_weeks')
        if duration_weeks and len(v) != duration_weeks:
            raise ValueError(f"Expected {duration_weeks} weeks, got {len(v)}")
        
        # Check week numbers are sequential
        week_numbers = [week.week_number for week in v]
        expected_weeks = list(range(1, len(v) + 1))
        
        if sorted(week_numbers) != expected_weeks:
            raise ValueError("Week numbers must be sequential starting from 1")
        
        return v
    
    def validate_structure(self):
        """Additional validation for plan structure"""
        total_days = sum(len(week.days) for week in self.weeks)
        expected_days = self.duration_weeks * 7
        
        if total_days != expected_days:
            raise ValueError(f"Expected {expected_days} total days, got {total_days}")
        
        # Count exercises across all weeks
        total_exercises = 0
        total_rest_days = 0
        
        for week in self.weeks:
            for day in week.days:
                if day.is_rest_day:
                    total_rest_days += 1
                else:
                    total_exercises += len(day.exercises)
        
        # Sanity check: should have some exercises and some rest
        if total_exercises < self.duration_weeks * 10:  # At least ~10 exercises per week
            raise ValueError("Plan seems to have too few exercises")
        
        if total_rest_days == 0:
            raise ValueError("Plan should include rest days")


def validate_ai_plan_response(raw_response: str) -> WorkoutPlan:
    """
    Validate and parse AI plan response with strict error handling
    
    Args:
        raw_response: Raw JSON string from AI
        
    Returns:
        Validated WorkoutPlan object
        
    Raises:
        ValidationError: If response doesn't match schema
        ValueError: If structure validation fails
        JSONDecodeError: If JSON is malformed
    """
    import json
    
    # Parse JSON
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from AI: {str(e)}")
    
    # Validate with Pydantic
    try:
        plan = WorkoutPlan.model_validate(data)
    except ValidationError as e:
        error_details = []
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error['loc'])
            error_details.append(f"{loc}: {error['msg']}")
        raise ValueError(f"AI response validation failed: {'; '.join(error_details)}")
    
    # Additional structure validation
    try:
        plan.validate_structure()
    except ValueError as e:
        raise ValueError(f"Plan structure validation failed: {str(e)}")
    
    return plan


# Additional schemas for other AI responses

class WeeklyAdaptation(BaseModel):
    """Schema for weekly plan adaptation"""
    week_number: int = Field(..., ge=1, le=12)
    adaptations: Dict[str, Any] = Field(..., description="Adaptation changes")
    reasoning: str = Field(..., min_length=20, max_length=500)


class ExerciseRecommendation(BaseModel):
    """Schema for exercise recommendations"""
    original_exercise: str
    recommended_alternatives: List[str] = Field(..., min_length=1, max_length=5)
    reasoning: str = Field(..., min_length=10, max_length=300)