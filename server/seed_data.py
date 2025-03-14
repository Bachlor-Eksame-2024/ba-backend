from faker import Faker
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import Base, engine, get_db
from models import (
    UserRoles,
    FitnessCenters,
    Users,
    Boxes,
    Bookings,
    BookingAvailabilities,
    Workout,
    Week,
    Exercise,
    StripePayment,
)

from datetime import datetime, timedelta
import random
import string
from typing import List
from authentication.authentications import get_current_user
from pydantic import BaseModel

fake = Faker()
seed_router = APIRouter()

# Set the date range
start_date = datetime.now() - timedelta(days=30)
end_date = datetime.now() + timedelta(days=10)


def create_user_roles(db: Session):
    roles = [UserRoles(role_name="admin"), UserRoles(role_name="user")]
    for role in roles:
        db.add(role)
    db.commit()


def create_boxes(
    db: Session, fitness_centers: List[FitnessCenters], num_boxes: int = 200
):
    boxes = []
    # Distribute boxes evenly among fitness centers
    for i in range(num_boxes):
        box = Boxes(
            box_number=i + 1,
            created_at=datetime.now(),
            box_availability="Ledigt",
            fitness_center_fk=fitness_centers[
                i % len(fitness_centers)
            ].fitness_center_id,
        )
        db.add(box)
        db.flush()
        boxes.append(box)
    return boxes


def create_fitness_centers(db: Session):
    centers_names = [
        "Fitness X",
        "SATS",
        "Puregym",
        "Fit & Sund",
        "Loop Fitness",
        "Copenhagen Gym",
        "Power House",
        "Ground",
    ]

    created_centers = []
    for center_name in centers_names:
        center = FitnessCenters(
            fitness_center_name=center_name, fitness_center_address=fake.address()
        )
        db.add(center)
        created_centers.append(center)

    db.commit()
    return created_centers


def create_users(db: Session, centers, roles, num_users: int = 1200):
    users = []
    for _ in range(num_users):
        user = Users(
            user_first_name=fake.first_name(),
            user_last_name=fake.last_name(),
            user_email=fake.unique.email(),
            is_member=True,
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKxcQw8.CKYlB.m",
            is_verified=True,
            verification_token=None,
            user_phone=fake.unique.phone_number(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            user_role_fk=random.choice(roles).user_role_id,
            fitness_center_fk=random.choice(centers).fitness_center_id,
            # user_bookings_fk=None,
        )
        db.add(user)
        db.flush()
        users.append(user)
    return users


def create_bookings(db: Session, users, boxes, total_bookings: int = 9600):
    for _ in range(total_bookings):
        user = random.choice(users)
        start_hour = random.randint(8, 20)
        duration = random.randint(1, 4)
        end_hour = (start_hour + duration) % 24

        booking = Bookings(
            user_id=user.user_id,
            booking_box_id_fk=random.choice(boxes).box_id,
            booking_date=fake.date_time_between(
                start_date=start_date, end_date=end_date
            ),
            booking_code="".join(
                random.choices(string.ascii_uppercase + string.digits, k=4)
            ),
            booking_start_hour=start_hour,
            booking_duration_hours=duration,
            booking_end_hour=end_hour,
            booking_timestamp=datetime.now(),
        )
        db.add(booking)
        db.flush()

        # Update user's booking FK
        user.user_bookings_fk = booking.booking_id

    db.commit()


def create_booking_availabilities(db: Session, boxes):
    for box in boxes:
        for hour in range(24):  # 0 to 23 hours
            avail = BookingAvailabilities(
                box_id_fk=box.box_id,
                booking_date=fake.date_time_between(
                    start_date=start_date, end_date=end_date
                ),
                hour_of_day=hour,
                is_available=True,
            )
            db.add(avail)


@seed_router.post("/seed-database")
async def seed_database(db: Session = Depends(get_db)):
    try:
        # Create in correct order
        create_user_roles(db)
        fitness_centers = create_fitness_centers(db)
        boxes = create_boxes(db, fitness_centers)

        # Get roles for users
        roles = db.query(UserRoles).all()
        users = create_users(db, fitness_centers, roles)

        create_bookings(db, users, boxes)
        create_booking_availabilities(db, boxes)

        db.commit()
        return {"message": "Database seeded successfully"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}


class DeleteRequest(BaseModel):
    key: str


@seed_router.post("/recreate-tables")
async def delete_tables(
    request: DeleteRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if request.key != "åøæsåpflåapkdfåpasl234":
        return {"error": "Invalid key"}
    try:
        tables = [
            "exercises",
            "weeks",
            "workouts",
            "booking_availabilities",
            "bookings",
            "payments",
            "boxes",
            "users",
            "fitness_centers",
            "user_roles",
        ]

        for table in tables:
            db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))

        db.commit()
        Base.metadata.create_all(bind=engine)
        return {"message": "Tables Been Recreated successfully"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
