# JSON Schema for GPT-5 Responses API
# Compatible with VideoPlaylistBuilder expectations

WORKOUT_PLAN_JSON_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "WorkoutPlan",
    "type": "object",
    "additionalProperties": False,
    "required": ["duration_weeks", "weeks"],
    "properties": {
        "duration_weeks": {
            "type": "integer",
            "minimum": 4,
            "maximum": 12,
            "description": "Total number of weeks in the plan"
        },
        "goal": {
            "type": "string",
            "description": "Primary fitness goal"
        },
        "weeks": {
            "type": "array",
            "minItems": 4,
            "maxItems": 12,
            "items": {"$ref": "#/$defs/Week"}
        }
    },
    "$defs": {
        "Week": {
            "type": "object",
            "additionalProperties": False,
            "required": ["week_number", "days"],
            "properties": {
                "week_number": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 12
                },
                "week_focus": {
                    "type": "string",
                    "description": "Focus theme for the week"
                },
                "days": {
                    "type": "array",
                    "minItems": 7,
                    "maxItems": 7,
                    "items": {"$ref": "#/$defs/Day"}
                }
            }
        },
        "Day": {
            "type": "object",
            "additionalProperties": False,
            "required": ["day_number", "is_rest_day", "blocks"],
            "properties": {
                "day_number": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 7
                },
                "workout_name": {
                    "type": "string",
                    "description": "Name of the workout"
                },
                "is_rest_day": {
                    "type": "boolean"
                },
                "blocks": {
                    "type": "array",
                    "minItems": 0,
                    "items": {"$ref": "#/$defs/Block"}
                }
            }
        },
        "Block": {
            "type": "object",
            "additionalProperties": False,
            "required": ["type"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["warmup", "main", "cooldown", "confidence_task"],
                    "description": "Type of workout block"
                },
                "name": {
                    "type": "string",
                    "description": "Optional block name"
                },
                "exercises": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/Exercise"},
                    "description": "Exercises in this block (for warmup/main/cooldown)"
                },
                "text": {
                    "type": "string",
                    "maxLength": 500,
                    "description": "Text content for confidence_task blocks"
                },
                "description": {
                    "type": "string",
                    "maxLength": 500,
                    "description": "Block description or instructions"
                }
            }
        },
        "Exercise": {
            "type": "object",
            "additionalProperties": False,
            "required": ["slug", "sets", "reps"],
            "properties": {
                "slug": {
                    "type": "string",
                    "pattern": "^[A-Z0-9_]+$",
                    "description": "Exercise ID from CSVExercise.id (e.g., EX027_v2)"
                },
                "name": {
                    "type": "string",
                    "description": "Optional exercise name"
                },
                "sets": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10
                },
                "reps": {
                    "type": "string",
                    "description": "Repetitions (e.g., '8-12', '30 sec')"
                },
                "rest_seconds": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 600,
                    "description": "Rest time in seconds"
                },
                "duration_seconds": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 1800,
                    "description": "Exercise duration (optional)"
                }
            }
        }
    },
    "examples": [
        {
            "duration_weeks": 4,
            "goal": "strength_building",
            "weeks": [
                {
                    "week_number": 1,
                    "week_focus": "Foundation Building",
                    "days": [
                        {
                            "day_number": 1,
                            "workout_name": "Upper Body Strength",
                            "is_rest_day": False,
                            "blocks": [
                                {
                                    "type": "warmup",
                                    "name": "Dynamic Warm-up",
                                    "exercises": [
                                        {
                                            "slug": "EX001_v2",
                                            "name": "Arm Circles",
                                            "sets": 1,
                                            "reps": "30 sec",
                                            "rest_seconds": 15
                                        }
                                    ]
                                },
                                {
                                    "type": "main",
                                    "name": "Strength Training",
                                    "exercises": [
                                        {
                                            "slug": "EX027_v2",
                                            "name": "Push-ups",
                                            "sets": 3,
                                            "reps": "8-12",
                                            "rest_seconds": 60
                                        }
                                    ]
                                },
                                {
                                    "type": "confidence_task",
                                    "text": "Today, practice good posture for 5 minutes while working",
                                    "description": "Focus on building confidence through body awareness"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}