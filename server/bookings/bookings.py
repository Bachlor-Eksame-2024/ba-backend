from fastapi import APIRouter, Depends, HTTPException
from authentication.jwt import get_current_user
from datetime import datetime
from database import get_db
from sqlalchemy import func
from models import Bookings, Boxes
from bookings.types.booking_types import (
    BookingData,
    GetBooking,
    DeleteBooking,
    GetBookingTime,
)
import random


booking_router = APIRouter(dependencies=[Depends(get_current_user)])

###########################
#### GET USER BOOKINGS ####


@booking_router.post("/get-bookings")
def get_booking(user: GetBooking, db=Depends(get_db)):
    # Extract user_id from current_user
    user_id = user.user_id

    # Get current date
    today = datetime.now().date()

    # Get all bookings for the authenticated user from today onwards
    user_bookings = (
        db.query(Bookings)
        .filter(Bookings.user_id == user_id, func.date(Bookings.booking_date) >= today)
        .all()
    )

    # Convert SQLAlchemy objects to dict for JSON response
    bookings_list = [booking.__dict__ for booking in user_bookings]

    return {"status": "success", "bookings": bookings_list}


##################################
#### GET AVAILABLE TIME SLOTS ####
def does_time_overlap(start1: int, end1: int, start2: int, end2: int) -> bool:
    """Check if two time periods overlap"""
    return not (end1 <= start2 or start1 >= end2)


@booking_router.post("/get-available-time-slots")
def get_available_time_slots(
    getBookingTime: GetBookingTime,
    db=Depends(get_db),
):
    current_time = getBookingTime.current_time
    duration = getBookingTime.duration_hours
    fitness_center_id = getBookingTime.fitness_center_id
    date = getBookingTime.booking_date
    try:
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
                func.date(Bookings.booking_date) == date,
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
                        {
                            "start_hour": start_hour,
                            "end_hour": end_hour,
                        }
                    )

        # Remove boxes with no available slots
        available_boxes = {
            box_id: slots for box_id, slots in availability.items() if slots
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


############################
#### CREATE NEW BOOKING ####


@booking_router.post("/create-booking")
def create_booking(
    booking_data: BookingData,
    db=Depends(get_db),
):

    # Extract booking data
    user_id = booking_data.user_id
    box_id = booking_data.booking_box_id_fk
    booking_duration = booking_data.booking_duration_hours
    booking_code = "".join([str(random.randint(0, 9)) for _ in range(4)])
    booking_date = booking_data.booking_date
    start_time = booking_data.booking_start_hour
    end_time = booking_data.booking_end_hour

    # Create a new booking
    new_booking = Bookings(
        user_id=user_id,
        booking_box_id_fk=box_id,
        booking_date=booking_date,
        booking_code=booking_code,
        booking_start_hour=start_time,
        booking_duration_hours=booking_duration,
        booking_end_hour=end_time,
        booking_timestamp=datetime.now(),
    )

    # Add the new booking to the database
    db.add(new_booking)
    db.commit()

    return {"status": "success", "message": new_booking}


########################
#### DELETE BOOKING ####


@booking_router.post("/delete-booking/")
def delete_booking(delete_booking: DeleteBooking, db=Depends(get_db)):
    # Get the booking to delete
    booking_id = delete_booking.booking_id
    booking_to_delete = (
        db.query(Bookings).filter(Bookings.booking_id == booking_id).first()
    )
    # Check if the booking exists
    if not booking_to_delete:
        return {"status": "error", "message": "Booking not found"}

    # Delete the booking
    db.delete(booking_to_delete)
    db.commit()
    return {"status": "success", "message": "Booking deleted successfully"}
