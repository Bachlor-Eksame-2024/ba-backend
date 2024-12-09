from fastapi import APIRouter, Depends
from authentication.jwt import get_current_user
from datetime import timedelta, datetime, timezone
from database import get_db
from models import Bookings
from bookings.types.booking_types import BookingData, GetBooking
import random


## Create a new router, and make it depend on the get_current_user function
## get_current_user function check if the user is authenticated or not
booking_router = APIRouter(dependencies=[Depends(get_current_user)])

# Get all user bookings from current date
# delete user booking
# get available time slots for booking a room
# Create a new booking for a user


###########################
#### GET USER BOOKINGS ####


@booking_router.post("/get-bookings")
def get_booking(user: GetBooking, db=Depends(get_db)):
    # Extract user_id from current_user
    user_id = user.user_id

    # Get all bookings for the authenticated user
    user_bookings = db.query(Bookings).filter(Bookings.user_id == user_id).all()

    # Convert SQLAlchemy objects to dict for JSON response
    bookings_list = [booking.__dict__ for booking in user_bookings]

    return {"status": "success", "bookings": bookings_list}


##################################
#### GET AVAILABLE TIME SLOTS ####


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
""" 
@booking_router.delete("/delete-booking")
def delete_booking(booking_id: int, db=Depends(get_db)):
    # Get the booking to delete
    booking_to_delete = db.query(Bookings).filter(Bookings.booking_id == booking_id).first() """
