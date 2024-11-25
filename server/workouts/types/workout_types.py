# workout_types.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Exercise(BaseModel):
    exercise_name: str = Field(..., example="Bodyweight Squats (3 sets of 12)")
    exercise_description: str = Field(
        ..., example="Focus on proper form. Keep your back straight, chest up."
    )


class Week(BaseModel):
    week_id: Optional[int] = Field(0, example=1)
    week_name: str = Field(..., example="Week 1: Foundation of Fitness")
    week_description: str = Field(..., example="This week focuses on mastering form")
    exercises: List[Exercise]


class CreateWorkout(BaseModel):
    workout_id: Optional[int] = Field(0, example=1)
    workout_name: str = Field(..., example="Transform in 8 Weeks")
    workout_description: str = Field(..., example="This 8-week fitness guide...")
    workout_level: str = Field(..., example="Beginner-to-Intermediate")
    workout_weeks: List[Week]
    workout_image: Optional[str] = Field(None, example="https://example.com/image.jpg")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "workout_id": 0,
                "workout_name": "Transform in 8 Weeks",
                "workout_description": "This 8-week fitness guide...",
                "workout_level": "Beginner-to-Intermediate",
                "workout_weeks": [
                    {
                        "week_id": 0,
                        "week_name": "Week 1: Foundation of Fitness",
                        "week_description": "This week focuses on mastering form",
                        "exercises": [
                            {
                                "exercise_name": "Bodyweight Squats (3 sets of 12)",
                                "exercise_description": "Focus on proper form. Keep your back straight, chest up.",
                            }
                        ],
                    }
                ],
                "workout_image": "https://example.com/image.jpg",
                "created_at": "2024-11-25T22:59:55.571Z",
                "updated_at": "2024-11-25T22:59:55.571Z",
            }
        }
