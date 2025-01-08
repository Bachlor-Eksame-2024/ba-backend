from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import Boxes, Bookings
from datetime import datetime, timedelta
from admin.types.admin_types import (
    BoksUpdate,
    BoxAvailabilityResponse,
    BoxResponse,
    BoxAvailabilityByIdResponse,
)
import random
import string


boxes_router = APIRouter()


##############################
#### GET BOX AVALIABLILTY ####


def does_time_overlap(start1: int, end1: int, start2: int, end2: int) -> bool:
    """Check if two time periods overlap"""
    return not (end1 <= start2 or start1 >= end2)


@boxes_router.get(
    "/box-availability/{fitness_center_id}/{date}/{current_time}/{duration}",
    response_model=BoxAvailabilityResponse,
)
def get_box_availability(
    db: Session = Depends(get_db),
    fitness_center_id: int = Path(..., description="ID of the fitness center"),
    date: str = Path(..., description="Date to check availability"),
    current_time: str = Path(..., description="Current time in HHMM format"),
    duration: int = Path(..., ge=1, le=4, description="Duration in hours (1-4)"),
):
    current_time = f"{current_time[:2]}:{current_time[2:]}"
    try:
        # Parse date string to datetime
        date_obj = datetime.strptime(date, "%Y-%m-%d")

        # Format time string correctly (HHMM to HH:MM)
        formatted_time = f"{current_time[:2]}:{current_time[2:]}"
        # Parse current time and get next available hour
        current_hour = datetime.strptime(current_time, "%H:%M").hour
        next_available_hour = current_hour + 1 if current_hour < 23 else None

        if next_available_hour is None:
            return {"message": "No more bookings available today"}

        # Get all boxes for the fitness center
        boxes = (
            db.query(Boxes).filter(Boxes.fitness_center_fk == fitness_center_id).all()
        )

        # Get existing bookings for the date
        bookings = (
            db.query(Bookings)
            .filter(
                Bookings.booking_box_id_fk.in_([box.box_id for box in boxes]),
                func.date(Bookings.booking_date) == date_obj.date(),
            )
            .all()
        )

        availability = {}
        for box in boxes:
            availability[box.box_id] = []

            # Check each possible starting hour
            for start_hour in range(next_available_hour, 24 - duration + 1):
                end_hour = start_hour + duration
                is_available = True

                # Check against all existing bookings
                for booking in bookings:
                    if booking.booking_box_id_fk == box.box_id:
                        if does_time_overlap(
                            start_hour,
                            end_hour,
                            booking.booking_start_hour,
                            booking.booking_start_hour + booking.booking_duration_hours,
                        ):
                            is_available = False
                            break

                if is_available:
                    availability[box.box_id].append(
                        {"start_hour": start_hour, "end_hour": end_hour}
                    )

        # Remove boxes with no available slots
        available_boxes = {
            str(box_id): [
                {"start_hour": slot["start_hour"], "end_hour": slot["end_hour"]}
                for slot in slots
            ]
            for box_id, slots in availability.items()
            if slots
        }

        return {
            "next_available_hour": next_available_hour,
            "duration_hours": duration,
            "box_availability": available_boxes,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking availability: {str(e)}"
        )


#######################
#### GET ALL BOKS ####


@boxes_router.get("/box/{fitness_center_id}", response_model=BoxResponse)
def get_all_boks(
    fitness_center_id: int = Path(..., description="ID of the fitness center"),
    db: Session = Depends(get_db),
):
    # Get current time and calculate next hour
    current_time = datetime.now()
    next_hour = (
        (current_time + timedelta(hours=1))
        .replace(minute=0, second=0, microsecond=0)
        .hour
    )
    today = current_time.date()

    # Get all boxes
    boxes = db.query(Boxes).filter(Boxes.fitness_center_fk == fitness_center_id).all()

    # Get bookings that overlap with next hour
    booked_box_ids = (
        db.query(Bookings.booking_box_id_fk)
        .filter(
            func.date(Bookings.booking_date) == today,
            Bookings.booking_start_hour
            <= next_hour,  # Booking starts before or at next hour
            (Bookings.booking_start_hour + Bookings.booking_duration_hours)
            > next_hour,  # Booking ends after next hour
        )
        .all()
    )

    # Convert to set for O(1) lookup
    booked_box_ids = {box_id for (box_id,) in booked_box_ids}

    # Update box availability based on bookings
    response_boxes = [
        {
            "box_id": box.box_id,
            "created_at": box.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "box_number": box.box_number,
            "box_availability": box.box_availability,
            "fitness_center_fk": box.fitness_center_fk,
        }
        for box in boxes
    ]

    return {"boks": response_boxes}


#######################
#### GET ALL BOKS ####


@boxes_router.get(
    "/available-box/{fitness_center_id}/{boks_id}",
    response_model=BoxAvailabilityByIdResponse,
)
def get_boks_avaliability_by_id(
    db: Session = Depends(get_db),
    fitness_center_id: int = Path(..., description="ID of the fitness center"),
    boks_id: int = Path(..., description="ID of the box"),
):
    try:
        today = datetime.now().date()
        date_range = [today + timedelta(days=x) for x in range(7)]

        # Get box and bookings
        box = (
            db.query(Boxes)
            .filter(
                Boxes.fitness_center_fk == fitness_center_id, Boxes.box_id == boks_id
            )
            .first()
        )

        if not box:
            raise HTTPException(status_code=404, detail="Box not found")

        bookings = (
            db.query(Bookings)
            .filter(
                Bookings.booking_box_id_fk == boks_id,
                func.date(Bookings.booking_date) >= today,
                func.date(Bookings.booking_date) <= date_range[-1],
            )
            .all()
        )

        # Create availability map
        dates_dict = {}
        for date in date_range:
            date_str = date.strftime("%Y-%m-%d")
            dates_dict[date_str] = {
                str(hour): {"available": True, "booking": None} for hour in range(24)
            }

        # Mark booked slots
        for booking in bookings:
            booking_date = booking.booking_date.strftime("%Y-%m-%d")
            if booking_date in dates_dict:
                for hour in range(
                    booking.booking_start_hour,
                    booking.booking_start_hour + booking.booking_duration_hours,
                ):
                    if hour < 24:
                        dates_dict[booking_date][str(hour)] = {
                            "available": False,
                            "booking": {
                                "booking_id": booking.booking_id,
                                "start_hour": booking.booking_start_hour,
                                "duration": booking.booking_duration_hours,
                                "end_hour": booking.booking_start_hour
                                + booking.booking_duration_hours,
                            },
                        }

        return {"box_id": box.box_id, "dates": dates_dict}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


###########################
#### GET BOOKING BY ID ####


@boxes_router.put("/box-status")
def update_boks_status(boks_update: BoksUpdate, db: Session = Depends(get_db)):
    print(boks_update, flush=True)
    try:
        # Get current time info
        current_time = datetime.now()

        # Calculate nearest whole hour
        minutes = current_time.minute
        nearest_hour = current_time.replace(minute=0, second=0, microsecond=0)
        if minutes >= 30:
            nearest_hour = nearest_hour + timedelta(hours=1)

        current_hour = nearest_hour.hour
        today = current_time.date()

        # Rest of the code remains the same
        box = (
            db.query(Boxes)
            .filter(
                Boxes.box_id == int(boks_update.boks_id),
                Boxes.fitness_center_fk == int(boks_update.fitness_center_id),
            )
            .first()
        )

        if not box:
            raise HTTPException(status_code=404, detail="Box not found")

        # Find and delete existing bookings
        existing_bookings = (
            db.query(Bookings)
            .filter(
                Bookings.booking_box_id_fk == box.box_id,
                func.date(Bookings.booking_date) == today,
                Bookings.booking_start_hour <= current_hour,
                (Bookings.booking_start_hour + Bookings.booking_duration_hours)
                > current_hour,
            )
            .all()
        )

        for booking in existing_bookings:
            db.delete(booking)

        if boks_update.boks_availability == "Ledigt":
            box.box_availability = "Ledigt"

        elif boks_update.boks_availability.startswith("Lukket:"):
            duration = int(
                boks_update.boks_availability.split(":")[1].strip().replace("t", "")
            )
            booking_code = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=4)
            )

            new_booking = Bookings(
                user_id=boks_update.user_id,
                booking_box_id_fk=box.box_id,
                booking_date=nearest_hour,
                booking_code=booking_code,
                booking_start_hour=current_hour,
                booking_duration_hours=duration,
                booking_end_hour=(current_hour + duration) % 24,
                booking_timestamp=current_time,
            )

            db.add(new_booking)
            # Update to use original status text
            box.box_availability = boks_update.boks_availability

        db.commit()
        return {"message": "Box status updated successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error updating box status: {str(e)}"
        )
