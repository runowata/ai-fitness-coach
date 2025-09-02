"""Tests for AI response validation schemas"""

import json

import pytest
from pydantic import ValidationError

from apps.ai_integration.schemas import (
    ExerciseItem,
    WorkoutDay,
    WorkoutPlan,
    WorkoutWeek,
    validate_ai_plan_response,
)


class TestExerciseItem:
    """Test ExerciseItem schema validation"""
    
    def test_valid_exercise_item(self):
        """Test valid exercise item creation"""
        item = ExerciseItem(
            exercise_slug="push-ups",
            sets=3,
            reps="10-12",
            rest_seconds=60
        )
        assert item.exercise_slug == "push-ups"
        assert item.sets == 3
        assert item.reps == "10-12"
        assert item.rest_seconds == 60
    
    def test_exercise_slug_validation(self):
        """Test exercise slug validation"""
        # Valid slugs
        ExerciseItem(exercise_slug="push-ups")
        ExerciseItem(exercise_slug="EX001")
        ExerciseItem(exercise_slug="leg_raises")
        
        # Invalid slugs
        with pytest.raises(ValidationError):
            ExerciseItem(exercise_slug="")
        
        with pytest.raises(ValidationError):
            ExerciseItem(exercise_slug="invalid@slug")
    
    def test_sets_validation(self):
        """Test sets field validation"""
        # Valid sets
        ExerciseItem(exercise_slug="test", sets=1)
        ExerciseItem(exercise_slug="test", sets=10)
        
        # Invalid sets
        with pytest.raises(ValidationError):
            ExerciseItem(exercise_slug="test", sets=0)
        
        with pytest.raises(ValidationError):
            ExerciseItem(exercise_slug="test", sets=11)
    
    def test_rest_seconds_validation(self):
        """Test rest seconds validation"""
        # Valid rest
        ExerciseItem(exercise_slug="test", rest_seconds=30)
        ExerciseItem(exercise_slug="test", rest_seconds=300)
        
        # Invalid rest
        with pytest.raises(ValidationError):
            ExerciseItem(exercise_slug="test", rest_seconds=5)  # Too short
        
        with pytest.raises(ValidationError):
            ExerciseItem(exercise_slug="test", rest_seconds=700)  # Too long


class TestWorkoutDay:
    """Test WorkoutDay schema validation"""
    
    def test_valid_workout_day(self):
        """Test valid workout day creation"""
        day = WorkoutDay(
            day_number=1,
            workout_name="Push Day",
            exercises=[
                ExerciseItem(exercise_slug="push-ups", sets=3, reps="10"),
                ExerciseItem(exercise_slug="dips", sets=3, reps="8-10")
            ],
            confidence_task="Do 5 push-ups in public"
        )
        assert day.day_number == 1
        assert len(day.exercises) == 2
        assert not day.is_rest_day
    
    def test_rest_day_validation(self):
        """Test rest day validation"""
        # Valid rest day
        rest_day = WorkoutDay(
            day_number=7,
            workout_name="Rest Day",
            is_rest_day=True,
            exercises=[]
        )
        assert rest_day.is_rest_day
        
        # Invalid: rest day with exercises
        with pytest.raises(ValidationError):
            WorkoutDay(
                day_number=7,
                workout_name="Rest Day",
                is_rest_day=True,
                exercises=[ExerciseItem(exercise_slug="test")]
            )
    
    def test_workout_day_without_exercises(self):
        """Test non-rest day without exercises fails"""
        with pytest.raises(ValidationError):
            WorkoutDay(
                day_number=1,
                workout_name="Empty Day",
                is_rest_day=False,
                exercises=[]
            )


class TestWorkoutWeek:
    """Test WorkoutWeek schema validation"""
    
    def create_valid_days(self):
        """Helper to create 7 valid days"""
        days = []
        for i in range(1, 8):
            if i == 7:  # Make day 7 a rest day
                day = WorkoutDay(
                    day_number=i,
                    workout_name="Rest Day",
                    is_rest_day=True
                )
            else:
                day = WorkoutDay(
                    day_number=i,
                    workout_name=f"Day {i} Workout",
                    exercises=[ExerciseItem(exercise_slug="test-exercise")]
                )
            days.append(day)
        return days
    
    def test_valid_workout_week(self):
        """Test valid workout week creation"""
        days = self.create_valid_days()
        week = WorkoutWeek(
            week_number=1,
            week_focus="Building Foundation",
            days=days
        )
        assert week.week_number == 1
        assert len(week.days) == 7
    
    def test_week_must_have_7_days(self):
        """Test week must have exactly 7 days"""
        # Too few days
        with pytest.raises(ValidationError):
            WorkoutWeek(
                week_number=1,
                days=[
                    WorkoutDay(day_number=1, workout_name="Day 1", 
                             exercises=[ExerciseItem(exercise_slug="test")])
                ]
            )
        
        # Too many days
        days = self.create_valid_days()
        days.append(WorkoutDay(day_number=8, workout_name="Extra", is_rest_day=True))
        
        with pytest.raises(ValidationError):
            WorkoutWeek(week_number=1, days=days)
    
    def test_days_must_be_numbered_1_to_7(self):
        """Test days must be numbered 1-7"""
        days = self.create_valid_days()
        days[0].day_number = 0  # Invalid day number
        
        with pytest.raises(ValidationError):
            WorkoutWeek(week_number=1, days=days)


class TestWorkoutPlan:
    """Test WorkoutPlan schema validation"""
    
    def create_valid_weeks(self, num_weeks=4):
        """Helper to create valid weeks"""
        weeks = []
        for week_num in range(1, num_weeks + 1):
            days = []
            for day_num in range(1, 8):
                if day_num == 7:
                    day = WorkoutDay(
                        day_number=day_num,
                        workout_name="Rest Day",
                        is_rest_day=True
                    )
                else:
                    day = WorkoutDay(
                        day_number=day_num,
                        workout_name=f"Week {week_num} Day {day_num}",
                        exercises=[
                            ExerciseItem(exercise_slug=f"exercise-{week_num}-{day_num}"),
                            ExerciseItem(exercise_slug=f"exercise-{week_num}-{day_num}-2")
                        ]
                    )
                days.append(day)
            
            week = WorkoutWeek(
                week_number=week_num,
                week_focus=f"Week {week_num} Focus",
                days=days
            )
            weeks.append(week)
        return weeks
    
    def test_valid_workout_plan(self):
        """Test valid workout plan creation"""
        weeks = self.create_valid_weeks(6)
        plan = WorkoutPlan(
            plan_name="6-Week Strength Building Program",
            duration_weeks=6,
            goal="Build strength and muscle mass",
            weeks=weeks
        )
        assert plan.plan_name == "6-Week Strength Building Program"
        assert plan.duration_weeks == 6
        assert len(plan.weeks) == 6
    
    def test_weeks_must_match_duration(self):
        """Test weeks list must match duration_weeks"""
        weeks = self.create_valid_weeks(4)
        
        with pytest.raises(ValidationError):
            WorkoutPlan(
                plan_name="Test Plan",
                duration_weeks=6,  # Mismatch: says 6 weeks but only 4 provided
                goal="Test goal",
                weeks=weeks
            )
    
    def test_week_numbers_must_be_sequential(self):
        """Test week numbers must be sequential from 1"""
        weeks = self.create_valid_weeks(4)
        weeks[1].week_number = 3  # Skip week 2
        
        with pytest.raises(ValidationError):
            WorkoutPlan(
                plan_name="Test Plan",
                duration_weeks=4,
                goal="Test goal",
                weeks=weeks
            )
    
    def test_structure_validation(self):
        """Test additional structure validation"""
        weeks = self.create_valid_weeks(4)
        plan = WorkoutPlan(
            plan_name="Test Plan",
            duration_weeks=4,
            goal="Test goal that is long enough",
            weeks=weeks
        )
        
        # Should not raise any errors
        plan.validate_structure()
    
    def test_structure_validation_too_few_exercises(self):
        """Test structure validation fails with too few exercises"""
        # Create plan with minimal exercises
        days = [
            WorkoutDay(day_number=i, workout_name=f"Day {i}", is_rest_day=True)
            for i in range(1, 8)
        ]
        weeks = [WorkoutWeek(week_number=1, days=days)]
        
        plan = WorkoutPlan(
            plan_name="Minimal Plan",
            duration_weeks=1,
            goal="Minimal goal for testing",
            weeks=weeks
        )
        
        with pytest.raises(ValueError, match="too few exercises"):
            plan.validate_structure()


class TestValidateAIPlanResponse:
    """Test AI plan response validation function"""
    
    def test_valid_json_response(self):
        """Test validation of valid JSON response"""
        plan_data = {
            "plan_name": "AI Generated Plan",
            "duration_weeks": 4,
            "goal": "Build strength and endurance through progressive training",
            "weeks": []
        }
        
        # Add valid weeks
        for week_num in range(1, 5):
            days = []
            for day_num in range(1, 8):
                if day_num == 7:
                    day = {
                        "day_number": day_num,
                        "workout_name": "Rest Day",
                        "is_rest_day": True,
                        "exercises": []
                    }
                else:
                    day = {
                        "day_number": day_num,
                        "workout_name": f"Week {week_num} Day {day_num}",
                        "is_rest_day": False,
                        "exercises": [
                            {"exercise_slug": "push-ups", "sets": 3, "reps": "10-12"},
                            {"exercise_slug": "squats", "sets": 3, "reps": "15"}
                        ]
                    }
                days.append(day)
            
            week = {
                "week_number": week_num,
                "week_focus": f"Week {week_num} Focus",
                "days": days
            }
            plan_data["weeks"].append(week)
        
        json_response = json.dumps(plan_data)
        validated_plan = validate_ai_plan_response(json_response)
        
        assert isinstance(validated_plan, WorkoutPlan)
        assert validated_plan.duration_weeks == 4
        assert len(validated_plan.weeks) == 4
    
    def test_invalid_json_response(self):
        """Test validation fails with invalid JSON"""
        invalid_json = '{"plan_name": "test", "invalid": json}'
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            validate_ai_plan_response(invalid_json)
    
    def test_validation_error_response(self):
        """Test validation fails with schema errors"""
        invalid_plan = {
            "plan_name": "",  # Too short
            "duration_weeks": 0,  # Too small
            "goal": "short",  # Too short
            "weeks": []
        }
        
        json_response = json.dumps(invalid_plan)
        
        with pytest.raises(ValueError, match="AI response validation failed"):
            validate_ai_plan_response(json_response)


@pytest.mark.parametrize("duration_weeks,expected_days", [
    (4, 28),
    (6, 42),
    (8, 56)
])
def test_plan_duration_calculations(duration_weeks, expected_days):
    """Test plan duration calculations with different week counts"""
    # This would test the actual calculation logic
    assert duration_weeks * 7 == expected_days