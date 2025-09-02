"""
GPT-5 Structured Outputs schemas using Pydantic
Ensures strict JSON schema adherence with guaranteed parsing
"""

from pydantic import BaseModel, Field
from typing import List
import re


class DailyWorkout(BaseModel):
    """Single day workout structure with exercise codes only"""
    day_number: int = Field(description="Day number within the week (1-7)")
    warmup_exercises: List[str] = Field(
        description="2 warmup/mobility exercise codes (WZ001-WZ021)",
        min_items=2,
        max_items=2
    )
    main_exercises: List[str] = Field(
        description="3-5 main strength/movement exercise codes (EX001-EX063)",
        min_items=3,
        max_items=5
    )
    endurance_exercises: List[str] = Field(
        description="1-2 cardio/conditioning exercise codes (SX001-SX021)",
        min_items=1,
        max_items=2
    )
    cooldown_exercises: List[str] = Field(
        description="2 cooldown/flexibility exercise codes (CZ001-CZ021)",
        min_items=2,
        max_items=2
    )

    def validate_exercise_codes(self):
        """Validate all exercise codes match expected patterns"""
        patterns = {
            'warmup': re.compile(r'^WZ\d{3}$'),
            'main': re.compile(r'^EX\d{3}$'),
            'endurance': re.compile(r'^SX\d{3}$'),
            'cooldown': re.compile(r'^CZ\d{3}$|^CX\d{3}$')  # Allow both CZ and CX for cooldown
        }
        
        # Validate warmup
        for code in self.warmup_exercises:
            if not patterns['warmup'].match(code):
                raise ValueError(f"Invalid warmup code: {code}")
                
        # Validate main
        for code in self.main_exercises:
            if not patterns['main'].match(code):
                raise ValueError(f"Invalid main code: {code}")
                
        # Validate endurance
        for code in self.endurance_exercises:
            if not patterns['endurance'].match(code):
                raise ValueError(f"Invalid endurance code: {code}")
                
        # Validate cooldown
        for code in self.cooldown_exercises:
            if not patterns['cooldown'].match(code):
                raise ValueError(f"Invalid cooldown code: {code}")


class WorkoutWeek(BaseModel):
    """Single week of workouts"""
    week_number: int = Field(description="Week number within the program (1-8)")
    focus: str = Field(description="Training focus for this week (e.g., 'Foundation', 'Development', 'Integration')")
    days: List[DailyWorkout] = Field(
        description="7 daily workouts for the week",
        min_items=7,
        max_items=7
    )

    def validate_days(self):
        """Ensure exactly 7 days numbered 1-7"""
        if len(self.days) != 7:
            raise ValueError("Must have exactly 7 days per week")
        
        expected_days = set(range(1, 8))
        actual_days = set(day.day_number for day in self.days)
        
        if actual_days != expected_days:
            raise ValueError(f"Days must be numbered 1-7, got: {actual_days}")


class WorkoutPlan(BaseModel):
    """Complete workout plan structure for GPT-5 Structured Outputs"""
    plan_name: str = Field(description="Descriptive name for the workout plan")
    duration_weeks: int = Field(
        description="Total duration in weeks (EXACTLY 3 weeks for exercise coverage)",
        ge=3,
        le=3
    )
    goal: str = Field(description="Primary training goal")
    weeks: List[WorkoutWeek] = Field(description="Weekly workout structure")

    def validate_structure(self):
        """Validate complete plan structure"""
        if len(self.weeks) != self.duration_weeks:
            raise ValueError(f"Must have {self.duration_weeks} weeks, got {len(self.weeks)}")
        
        expected_weeks = set(range(1, self.duration_weeks + 1))
        actual_weeks = set(week.week_number for week in self.weeks)
        
        if actual_weeks != expected_weeks:
            raise ValueError(f"Weeks must be numbered 1-{self.duration_weeks}, got: {actual_weeks}")
        
        # Validate each week
        for week in self.weeks:
            week.validate_days()
            for day in week.days:
                day.validate_exercise_codes()

    class Config:
        """Pydantic configuration"""
        str_strip_whitespace = True
        validate_assignment = True
        extra = "forbid"  # Don't allow extra fields


# Convenience function for schema generation
def get_workout_plan_schema():
    """Get JSON schema for GPT-5 Structured Outputs"""
    return WorkoutPlan.schema()


# Example usage for testing
if __name__ == "__main__":
    # Generate schema
    schema = get_workout_plan_schema()
    
    # Print schema for inspection
    import json
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Schema generated: {json.dumps(schema, indent=2)}")
    
    # Test validation with sample data
    sample_day = DailyWorkout(
        day_number=1,
        warmup_exercises=["WZ001", "WZ002"],
        main_exercises=["EX001", "EX005", "EX010"],
        endurance_exercises=["SX001"],
        cooldown_exercises=["CZ001", "CZ002"]
    )
    
    sample_week = WorkoutWeek(
        week_number=1,
        focus="Foundation",
        days=[sample_day] * 7  # Simplified for testing
    )
    
    sample_plan = WorkoutPlan(
        plan_name="Test Plan",
        duration_weeks=1,
        goal="test",
        weeks=[sample_week]
    )
    
    logger.info("Schema validation successful!")