# JSON Schema for GPT-5 Responses API
# Compatible with VideoPlaylistBuilder expectations

# New schema with report first, then plan
PLAN_WITH_REPORT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "WorkoutPlanWithReport",
    "type": "object",
    "additionalProperties": False,
    "required": ["report", "plan"],
    "properties": {
        "report": {
            "type": "object",
            "required": ["intro", "analysis", "recommendations", "safety_notes"],
            "properties": {
                "intro": {
                    "type": "string",
                    "minLength": 100,
                    "description": "Motivational introduction based on user's goals and context"
                },
                "analysis": {
                    "type": "string",
                    "minLength": 200,
                    "description": "Analysis of user's current state and needs"
                },
                "recommendations": {
                    "type": "array",
                    "minItems": 3,
                    "items": {
                        "type": "string",
                        "description": "Specific recommendations for success"
                    }
                },
                "safety_notes": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "string",
                        "description": "Safety considerations based on user's health conditions"
                    }
                },
                "weekly_progression": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 3,
                    "items": {
                        "type": "object",
                        "required": ["week", "focus", "explanation"],
                        "properties": {
                            "week": {"type": "integer", "minimum": 1, "maximum": 3},
                            "focus": {"type": "string"},
                            "explanation": {"type": "string"}
                        }
                    }
                }
            }
        },
        "plan": {
            "$ref": "#/$defs/SimplePlan"
        }
    },
    "$defs": {
        "SimplePlan": {
            "type": "object",
            "required": ["weeks"],
            "properties": {
                "weeks": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 3,
                    "items": {
                        "type": "object",
                        "required": ["days"],
                        "properties": {
                            "days": {
                                "type": "array",
                                "minItems": 7,
                                "maxItems": 7,
                                "items": {
                                    "type": "object",
                                    "required": ["exercise_slugs", "is_rest_day"],
                                    "properties": {
                                        "exercise_slugs": {
                                            "type": "array",
                                            "description": "List of exercise slugs for the day",
                                            "items": {"type": "string"}
                                        },
                                        "is_rest_day": {
                                            "type": "boolean",
                                            "description": "True if this is a rest/recovery day"
                                        },
                                        "confidence_task": {
                                            "type": "string",
                                            "description": "Optional confidence-building task for the day"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

WORKOUT_PLAN_JSON_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "WorkoutPlan",
    "type": "object",
    "additionalProperties": False,
    "required": ["plan_name", "duration_weeks", "weeks", "goal"],
    "properties": {
        "plan_name": {
            "type": "string",
            "minLength": 5,
            "maxLength": 200,
            "description": "Name of the workout plan"
        },
        "duration_weeks": {
            "type": "integer",
            "minimum": 2,
            "maximum": 12,
            "description": "Total number of weeks in the plan"
        },
        "goal": {
            "type": "string",
            "description": "Primary fitness goal"
        },
        "weeks": {
            "type": "array",
            "minItems": 2,
            "maxItems": 12,
            "items": {"$ref": "#/$defs/Week"}
        }
    },
    "$defs": {
        "Week": {
            "type": "object",
            "additionalProperties": False,
            "required": ["week_number", "week_focus", "days"],
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
            "required": ["day_number", "workout_name", "is_rest_day", "blocks"],
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
            "required": ["type", "name", "exercises", "text", "description"],
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
            "required": ["exercise_slug", "sets", "reps", "name", "rest_seconds", "duration_seconds"],
            "properties": {
                "exercise_slug": {
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
                                            "exercise_slug": "EX001_v2",
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
                                            "exercise_slug": "EX027_v2",
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