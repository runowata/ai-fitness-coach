from apps.workouts.schemas import WorkoutPlan, WorkoutPlanItem
import pytest


def test_plan_validation():
    good = {
        "user_id": "u123",
        "archetype": "222",
        "day": 3,
        "items": [
            {"exercise_id": "EX027_v2", "sets": 4, "reps": 10, "rest_sec": 45}
        ],
    }
    plan = WorkoutPlan.model_validate(good)
    assert plan.day == 3
    assert plan.archetype == "222"
    assert len(plan.items) == 1
    assert plan.items[0].exercise_id == "EX027_v2"


def test_plan_validation_bad_archetype():
    bad = {
        "user_id": "u123",
        "archetype": "999",  # Invalid archetype
        "day": 3,
        "items": [
            {"exercise_id": "EX027_v2", "sets": 4, "reps": 10, "rest_sec": 45}
        ],
    }
    try:
        WorkoutPlan.model_validate(bad)
        assert False, "Validation should fail"
    except Exception:
        assert True


def test_plan_validation_bad_day():
    bad = {
        "user_id": "u123",
        "archetype": "111",
        "day": 10,  # Invalid day (should be 1-7)
        "items": [
            {"exercise_id": "EX027_v2", "sets": 4, "reps": 10, "rest_sec": 45}
        ],
    }
    try:
        WorkoutPlan.model_validate(bad)
        assert False, "Validation should fail"
    except Exception:
        assert True


def test_workout_plan_item():
    item_data = {
        "exercise_id": "WZ001",
        "sets": 3,
        "reps": 15,
        "rest_sec": 30
    }
    item = WorkoutPlanItem.model_validate(item_data)
    assert item.exercise_id == "WZ001"
    assert item.sets == 3
    assert item.reps == 15
    assert item.rest_sec == 30