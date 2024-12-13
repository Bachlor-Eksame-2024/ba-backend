from pydantic import BaseModel, RootModel
from typing import List, Dict


class BookingData(BaseModel):
    user_id: int
    booking_box_id_fk: int
    booking_duration_hours: int
    booking_date: str
    booking_start_hour: int
    booking_end_hour: int



class GetBookingTime(BaseModel):
    fitness_center_id: int
    booking_date: str
    current_time: str
    duration_hours: int


class CurrentBookings(BaseModel):
    booking_id: int
    booking_date: str
    booking_code: str
    booking_duration_hours: int
    booking_timestamp: str
    user_id: int
    booking_box_id_fk: int
    booking_start_hour: int
    booking_end_hour: int


class BookingResponse(BaseModel):
    status: str
    bookings: list[CurrentBookings]


class TimeSlot(BaseModel):
    start_hour: int
    end_hour: int


class TimeSlotResponse(BaseModel):
    next_available_hour: int
    duration_hours: int
    box_availability: Dict[str, List[Dict[str, int]]]

class DeleteBookingResponse(BaseModel):
    status: str
    message: str