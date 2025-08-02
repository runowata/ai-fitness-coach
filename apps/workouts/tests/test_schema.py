from apps.workouts.schemas import WorkoutPlan, WorkoutPlanItem, VideoScript
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


def test_video_script_validation():
    good = {
        "exercise_id": "WZ001",
        "archetype": "111",
        "locale": "ru",
        "script": "Начнем с вращения таза. Мой совет: закройте глаза..."
    }
    video_script = VideoScript.model_validate(good)
    assert video_script.exercise_id == "WZ001"
    assert video_script.archetype == "111"
    assert video_script.locale == "ru"
    assert "вращения таза" in video_script.script


def test_video_script_bad_archetype():
    bad = {
        "exercise_id": "WZ001",
        "archetype": "999",  # Invalid archetype
        "locale": "ru",
        "script": "Test script"
    }
    try:
        VideoScript.model_validate(bad)
        assert False, "Validation should fail"
    except Exception:
        assert True


def test_video_script_bad_locale():
    bad = {
        "exercise_id": "WZ001",
        "archetype": "222",
        "locale": "fr",  # Invalid locale (not ru/en)
        "script": "Test script"
    }
    try:
        VideoScript.model_validate(bad)
        assert False, "Validation should fail"
    except Exception:
        assert True


def test_video_script_default_locale():
    data = {
        "exercise_id": "WZ001",
        "archetype": "333",
        "script": "Test script without locale"
    }
    video_script = VideoScript.model_validate(data)
    assert video_script.locale == "ru"  # Should default to ru