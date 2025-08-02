from pydantic import BaseModel, Field
from typing import List


class ExerciseSchema(BaseModel):
    id: str
    name_ru: str
    name_en: str | None = None
    level: str
    description: str | None = None
    muscle_group: str | None = None
    exercise_type: str | None = None
    ai_tags: List[str] = Field(default_factory=list)


class WorkoutPlanItem(BaseModel):
    exercise_id: str = Field(description="ID from Exercise")
    sets: int = 3
    reps: int = 12
    rest_sec: int = 60


class WorkoutPlan(BaseModel):
    user_id: str
    archetype: str = Field(pattern="^(111|222|333)$")
    day: int = Field(ge=1, le=7)
    items: List[WorkoutPlanItem]