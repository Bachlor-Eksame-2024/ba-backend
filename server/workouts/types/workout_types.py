from pydantic import BaseModel
from typing import List


class WorkoutWeek(BaseModel):
    week_number: int
    week_name: str
    week_description: str
    created_at: str
    updated_at: str


class Workout(BaseModel):
    workout_id: str
    workout_name: str
    workout_description: str
    workout_level: str
    workout_weeks: List[WorkoutWeek]
    created_at: str
    updated_at: str