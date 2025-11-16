Простая и надежная JSON Schema для GPT-5 
Только коды упражнений - все остальное собирается в коде

WORKOUT_PLAN_JSON_SCHEMA_SIMPLE = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "WorkoutPlan",
    "type": "object",
    "additionalProperties": False,
    "required": ["plan_name", "duration_weeks", "goal", "weeks"],
    "properties": {
        "plan_name": {
            "type": "string",
            "minLength": 10,
            "maxLength": 100,
            "description": "Название плана тренировок"
        },
        "duration_weeks": {
            "type": "integer",
            "minimum": 2,
            "maximum": 8,
            "description": "Длительность плана в неделях"
        },
        "goal": {
            "type": "string",
            "minLength": 20,
            "maxLength": 200,
            "description": "Основная цель плана"
        },
        "weeks": {
            "type": "array",
            "minItems": 2,
            "maxItems": 8,
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
                    "maximum": 8
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
            "required": ["day_number", "is_rest_day", "warmup_exercises", "main_exercises", "endurance_exercises", "cooldown_exercises"],
            "properties": {
                "day_number": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 7
                },
                "is_rest_day": {
                    "type": "boolean",
                    "description": "Является ли день отдыхом (если true, упражнения игнорируются)"
                },
                "warmup_exercises": {
                    "type": "array",
                    "minItems": 0,
                    "maxItems": 3,
                    "items": {
                        "type": "string",
                        "pattern": "^WZ\\d{3}(_v\\d+)?$",
                        "description": "Код упражнения разминки (например: WZ001, WZ015_v2)"
                    },
                    "description": "Коды упражнений для разминки (WZ001-WZ021)"
                },
                "main_exercises": {
                    "type": "array", 
                    "minItems": 0,
                    "maxItems": 6,
                    "items": {
                        "type": "string",
                        "pattern": "^EX\\d{3}(_v\\d+)?$",
                        "description": "Код основного упражнения (например: EX027, EX001_v2)"
                    },
                    "description": "Коды основных упражнений (EX001-EX063)"
                },
                "endurance_exercises": {
                    "type": "array",
                    "minItems": 0,
                    "maxItems": 3,
                    "items": {
                        "type": "string",
                        "pattern": "^SX\\d{3}(_v\\d+)?$",
                        "description": "Код упражнения на выносливость (например: SX001, SX005_v2)"
                    },
                    "description": "Коды упражнений сексуальной выносливости (SX001-SX021)"
                },
                "cooldown_exercises": {
                    "type": "array",
                    "minItems": 0,
                    "maxItems": 3,
                    "items": {
                        "type": "string", 
                        "pattern": "^CZ\\d{3}(_v\\d+)?$",
                        "description": "Код упражнения расслабления (например: CZ001, CZ010_v2)"
                    },
                    "description": "Коды упражнений расслабления/растяжки (CZ001-CZ021)"
                }
            }
        }
    },
    "examples": [
        {
            "plan_name": "Базовый план для начинающих",
            "duration_weeks": 4,
            "goal": "Развитие базовой силы и выносливости для начинающих",
            "weeks": [
                {
                    "week_number": 1,
                    "days": [
                        {
                            "day_number": 1,
                            "is_rest_day": False,
                            "warmup_exercises": ["WZ001", "WZ003"],
                            "main_exercises": ["EX027", "EX001", "EX015"],
                            "endurance_exercises": ["SX001", "SX005"],
                            "cooldown_exercises": ["CZ001", "CZ003"]
                        },
                        {
                            "day_number": 2,
                            "is_rest_day": False,
                            "warmup_exercises": ["WZ004", "WZ006"],
                            "main_exercises": ["EX003", "EX012", "EX025"],
                            "endurance_exercises": ["SX002"],
                            "cooldown_exercises": ["CZ002", "CZ004"]
                        },
                        {
                            "day_number": 3,
                            "is_rest_day": False,
                            "warmup_exercises": ["WZ005", "WZ007"],
                            "main_exercises": ["EX010", "EX020", "EX035"],
                            "endurance_exercises": ["SX003"],
                            "cooldown_exercises": ["CZ005", "CZ007"]
                        },
                        {
                            "day_number": 4,
                            "is_rest_day": False,
                            "warmup_exercises": ["WZ008", "WZ010"],
                            "main_exercises": ["EX006", "EX018", "EX032"],
                            "endurance_exercises": ["SX004"],
                            "cooldown_exercises": ["CZ006", "CZ008"]
                        },
                        {
                            "day_number": 5,
                            "is_rest_day": False,
                            "warmup_exercises": ["WZ002", "WZ008"],
                            "main_exercises": ["EX005", "EX030", "EX040"],
                            "endurance_exercises": ["SX010"],
                            "cooldown_exercises": ["CZ010", "CZ015"]
                        },
                        {
                            "day_number": 6,
                            "is_rest_day": False,
                            "warmup_exercises": ["WZ009", "WZ011"],
                            "main_exercises": ["EX008", "EX022", "EX038"],
                            "endurance_exercises": ["SX006"],
                            "cooldown_exercises": ["CZ009", "CZ012"]
                        },
                        {
                            "day_number": 7,
                            "is_rest_day": False,
                            "warmup_exercises": ["WZ012", "WZ014"],
                            "main_exercises": ["EX011", "EX026", "EX042"],
                            "endurance_exercises": ["SX008"],
                            "cooldown_exercises": ["CZ011", "CZ014"]
                        }
                    ]
                }
            ]
        }
    ]
}