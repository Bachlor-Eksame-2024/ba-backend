from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone

## this file contains the database models
## each model is a class that inherits from Base
## Base is a declarative_base instance from SQLAlchemy
## it is used to create the database tables


## User model - represents the users table in the database boksfit
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    # fitness_center_id = Column(Integer, ForeignKey("fitness_centers.fitness_center_id"))
    role = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationship example
    # items = relationship("Item", back_populates="owner")


##### WORKOUTS #####


class Workout(Base):
    __tablename__ = "workouts"

    workout_id = Column(Integer, primary_key=True, index=True)
    workout_name = Column(String(255), nullable=False)
    workout_description = Column(Text, nullable=False)
    workout_level = Column(String(50), nullable=False)
    workout_image = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    workout_weeks = relationship(
        "Week", back_populates="workout", cascade="all, delete-orphan"
    )


class Week(Base):
    __tablename__ = "weeks"

    week_id = Column(Integer, primary_key=True, index=True)
    workout_id = Column(
        Integer, ForeignKey("workouts.workout_id", ondelete="CASCADE"), nullable=False
    )
    week_name = Column(String(255), nullable=False)
    week_description = Column(Text, nullable=False)

    workout = relationship("Workout", back_populates="workout_weeks")
    exercises = relationship(
        "Exercise", back_populates="week", cascade="all, delete-orphan"
    )


class Exercise(Base):
    __tablename__ = "exercises"

    exercise_id = Column(Integer, primary_key=True, index=True)
    week_id = Column(
        Integer, ForeignKey("weeks.week_id", ondelete="CASCADE"), nullable=False
    )
    exercise_name = Column(String(255), nullable=False)
    exercise_description = Column(Text, nullable=False)

    week = relationship("Week", back_populates="exercises")
