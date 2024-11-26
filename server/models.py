from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone

## this file contains the database models
## each model is a class that inherits from Base
## Base is a declarative_base instance from SQLAlchemy
## it is used to create the database tables


class BookingAvailabilities(Base):
    __tablename__ = "booking_availablities"

    booking_availability_id = Column(
        Integer, primary_key=True, autoincrement=True, index=True, unique=True
    )
    box_id_fk = Column(Integer, ForeignKey("boxes.box_id"), nullable=False)
    booking_date = Column(DateTime, nullable=False)
    hour_of_day = Column(
        Integer, CheckConstraint("hour_of_day BETWEEN 0 AND 23"), nullable=False
    )
    is_available = Column(Boolean, nullable=False)

    boxes = relationship("Boxes", back_populates="booking_availablities")

class Boxes(Base):
    __tablename__ = "boxes"

    box_id = Column(
        Integer, primary_key=True, autoincrement=True, index=True, unique=True
    )
    box_number = Column(Integer, nullable=False, autoincrement=True, unique=True)
    created_at = Column(DateTime, nullable=False)


class Bookings(Base):
    __tablename__ = "bookings"

    booking_id = Column(
        Integer, primary_key=True, autoincrement=True, index=True, unique=True
    )
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    booking_box_id_fk = Column(
        Integer, ForeignKey("boxes.box_id", ondelete="CASCADE"), nullable=False
    )
    booking_date = Column(DateTime, nullable=False)
    booking_code = Column(String(4), nullable=False, unique=True)
    booking_start_hour = Column(
        Integer,
        CheckConstraint("booking_start_hour >= 0 AND booking_start_hour <= 23"),
        nullable=False,
    )
    booking_duration_hours = Column(
        Integer,
        CheckConstraint("booking_duration_hours >= 1 AND booking_duration_hours <= 4"),
        nullable=False,
    )
    booking_end_hour = Column(
        Integer,
        CheckConstraint("booking_end_hour >= 0 AND booking_end_hour <= 23"),
        nullable=False,
    )
    booking_timestamp = Column(DateTime, nullable=False)

    users = relationship("Users", back_populates="bookings")
    boxes = relationship("Boxes", back_populates="bookings")


class Users(Base):
    __tablename__ = "users"

    user_id = Column(
        Integer, primary_key=True, autoincrement=True, index=True, unique=True
    )
    user_first_name = Column(String(255), nullable=False)
    user_last_name = Column(String(255), nullable=False)
    password_hash = Column(String, nullable=False)
    user_phone = Column(String(255), nullable=False)
    create_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    user_role_fk = Column(Integer, ForeignKey("user_roles.user_role_id"), nullable=False)
    fitness_center_fk = Column(Integer, ForeignKey("fitness_centers.fitness_center_id"), nullable=False)
    user_bookings_fk = Column(Integer, ForeignKey("bookings.booking_id"), nullable=False)

    bookings = relationship("Bookings", back_populates="users")
    fitness_centers = relationship("FitnessCenters", back_populates="users")
    user_roles = relationship("UserRoles", back_populates="users")


class FitnessCenters(Base):
    __tablename__ = "fitness_centers"

    fitness_center_id = Column(
        Integer, primary_key=True, autoincrement=True, index=True, unique=True
    )
    fitness_center_name = Column(String(255), nullable=False)
    fitness_center_address = Column(String(255), nullable=False)
    fitness_boxes_fk = Column(Integer, ForeignKey("boxes.box_id"), nullable=False)
    
    boxes = relationship("Boxes", back_populates="fitness_centers")


class UserRoles(Base):
    __tablename__ = "user_roles"

    user_role_id = Column(
        Integer, primary_key=True, autoincrement=True, index=True, unique=True
    )
    role_name = Column(String(255), nullable=False)


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
