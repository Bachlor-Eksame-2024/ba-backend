from faker import Faker
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import (
    UserRoles,
    FitnessCenters,
    Users,
    Boxes,
    Bookings,
    BookingAvailabilities,
)
from datetime import datetime
import random
import string
from typing import List


fake = Faker()
seed_router = APIRouter()


def create_user_roles(db: Session):
    roles = ["admin", "user"]
    for role in roles:
        user_role = UserRoles(role_name=role)
        db.add(user_role)
    db.commit()


def create_boxes(
    db: Session, fitness_centers: List[FitnessCenters], num_boxes: int = 20
):
    boxes = []
    # Distribute boxes evenly among fitness centers
    for i in range(num_boxes):
        box = Boxes(
            box_number=i + 1,
            created_at=datetime.now(),
            box_availability="available",
            fitness_center_id=fitness_centers[
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


def create_users(db: Session, centers, roles, num_users: int = 100):
    users = []
    for _ in range(num_users):
        user = Users(
            user_first_name=fake.first_name(),
            user_last_name=fake.last_name(),
            user_email=fake.email(),
            is_member=True,
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKxcQw8.CKYlB.m",
            is_verified=True,
            verification_token=None,
            user_phone=fake.phone_number(),
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


def create_bookings(db: Session, users, boxes):
    for user in users:
        booking = Bookings(
            user_id=user.user_id,
            booking_box_id_fk=random.choice(boxes).box_id,
            booking_date=fake.date_time_between(start_date="now", end_date="+30d"),
            booking_code="".join(
                random.choices(string.ascii_uppercase + string.digits, k=4)
            ),
            booking_start_hour=random.randint(8, 20),
            booking_duration_hours=random.randint(1, 4),
            booking_end_hour=random.randint(9, 23),
            booking_timestamp=datetime.now(),
        )
        db.add(booking)
        db.flush()

        # Update user's booking FK
        user.user_bookings_fk = booking.booking_id


def create_booking_availabilities(db: Session, boxes):
    for box in boxes:
        for hour in range(24):  # 0 to 23 hours
            avail = BookingAvailabilities(
                box_id_fk=box.box_id,
                booking_date=fake.date_time_between(start_date="now", end_date="+30d"),
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
