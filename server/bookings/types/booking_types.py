from pydantic import BaseModel


class BookingData(BaseModel):
    user_id: int
    booking_box_id_fk: int
    booking_duration_hours: int
    booking_date: str
    booking_start_hour: int
    booking_end_hour: int


class GetBooking(BaseModel):
    user_id: int
