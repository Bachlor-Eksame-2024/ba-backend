from pydantic import BaseModel


class ChangePassword(BaseModel):
    user_id: str
    old_password: str
    new_password: str
    confirm_password: str


class UpdateProfile(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    fitness_center_id: str


class UserStats(BaseModel):
    user_id: str


class MonthlyStat(BaseModel):
    pv: int
    name: str


class WeeklyStat(BaseModel):
    pv: int
    name: str


class UserStatsResponse(BaseModel):
    total_bookings: int
    monthly_stats: list[MonthlyStat]
    weekly_stats: list[WeeklyStat]
