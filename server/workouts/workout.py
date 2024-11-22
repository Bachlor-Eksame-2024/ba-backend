import os
import json
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from database import get_db
from sqlalchemy.orm import Session
from authentication.jwt import get_current_user
from datetime import datetime
from models import Workout, Week, Exercise

workout_router = APIRouter()


def load_workouts(session: Session, data: list):
    week_id_counter = 1  # Counter for generating unique week_ids

    for workout_data in data:
        # Create workout
        workout = Workout(
            workout_id=int(workout_data["workout_id"]),
            workout_name=workout_data["workout_name"],
            workout_description=workout_data["workout_description"],
            workout_level=workout_data["workout_level"],
            workout_image=workout_data.get("workout_image"),
            created_at=datetime.fromisoformat(
                workout_data["created_at"].replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                workout_data["updated_at"].replace("Z", "+00:00")
            ),
        )
        session.add(workout)

        # Create weeks for each workout with unique week_ids
        for week_data in workout_data["workout_weeks"]:
            week = Week(
                week_id=week_id_counter,  # Use counter instead of week_data["week_id"]
                workout_id=int(workout_data["workout_id"]),
                week_name=week_data["week_name"],
                week_description=week_data["week_description"],
            )
            session.add(week)

            # Create exercises for each week
            for exercise_data in week_data["exercises"]:
                exercise = Exercise(
                    week_id=week_id_counter,  # Use the same counter for exercises
                    exercise_name=exercise_data["exercise_name"],
                    exercise_description=exercise_data["exercise_description"],
                )
                session.add(exercise)

            week_id_counter += 1  # Increment counter after each week

    session.commit()


@workout_router.post("/load-workouts")
async def initialize_workouts(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    try:
        # Debug: Print current working directory
        print(f"Current working directory: {os.getcwd()}", flush=True)

        # List files in current directory
        print(f"Files in directory: {os.listdir()}", flush=True)

        # Use path relative to mounted directory
        file_path = os.path.join(os.getcwd(), "workouts", "workouts.json")
        print(f"Trying to open file at: {file_path}", flush=True)

        with open(file_path, "r") as file:
            workout_data = json.load(file)

        load_workouts(db, workout_data)
        return JSONResponse(
            {"message": "Workouts loaded successfully"}, status_code=200
        )
    except Exception as e:
        print(f"Error loading workouts: {str(e)}", flush=True)
        return JSONResponse(
            {"error": f"Failed to load workouts: {str(e)}"}, status_code=500
        )


@workout_router.get("/get-workouts")
async def get_workouts(db: Session = Depends(get_db)):
    workouts = db.query(Workout).all()

    # Convert workouts to dictionary format
    workout_list = []
    for workout in workouts:
        workout_dict = {
            "workout_id": workout.workout_id,
            "workout_name": workout.workout_name,
            "workout_description": workout.workout_description,
            "workout_level": workout.workout_level,
            "workout_image": workout.workout_image,
            "created_at": workout.created_at.isoformat(),
            "updated_at": workout.updated_at.isoformat(),
            "workout_weeks": [],
        }

        # Add weeks for each workout
        for week in workout.workout_weeks:
            week_dict = {
                "week_id": week.week_id,
                "week_name": week.week_name,
                "week_description": week.week_description,
                "exercises": [],  # Initialize exercises list
            }

            # Query and add exercises for this week
            exercises = (
                db.query(Exercise).filter(Exercise.week_id == week.week_id).all()
            )
            for exercise in exercises:
                exercise_dict = {
                    "exercise_name": exercise.exercise_name,
                    "exercise_description": exercise.exercise_description,
                }
                week_dict["exercises"].append(exercise_dict)

            workout_dict["workout_weeks"].append(week_dict)

        workout_list.append(workout_dict)

    return JSONResponse({"workouts": workout_list}, status_code=200)
