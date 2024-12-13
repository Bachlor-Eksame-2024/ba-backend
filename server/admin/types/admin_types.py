from pydantic import BaseModel
from typing import Dict, List, Optional


class BoksUpdate(BaseModel):
    user_id: str
    fitness_center_id: str
    boks_id: str
    boks_availability: str


class User(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: str
    phone: str
    is_member: bool
    role: str


class UsersResponse(BaseModel):
    users: List[User]
    total: int
    page: int
    page_size: int
    total_pages: int


class DailyBooking(BaseModel):
    name: str
    pv: int


class StatsResponse(BaseModel):
    new_members_month: int
    new_members_today: int
    total_members: int
    total_boks: int
    checked_in_today: int
    daily_bookings: List[DailyBooking]


class TimeSlot(BaseModel):
    start_hour: int
    end_hour: int


class BoxAvailabilityResponse(BaseModel):
    next_available_hour: int
    duration_hours: int
    box_availability: Dict[str, List[TimeSlot]]


class Box(BaseModel):
    box_id: int
    created_at: str
    box_number: int
    box_availability: str
    fitness_center_fk: int


class BoxResponse(BaseModel):
    boks: List[Box]


class Booking(BaseModel):
    start_hour: int
    duration: int
    end_hour: int


class Booking(BaseModel):
    start_hour: int
    duration: int
    end_hour: int


class HourAvailability(BaseModel):
    available: bool
    booking: Optional[Booking] = None


class BoxAvailabilityByIdResponse(BaseModel):
    box_id: int
    dates: Dict[str, Dict[str, HourAvailability]]
