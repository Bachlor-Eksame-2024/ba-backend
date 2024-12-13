from pydantic import BaseModel
from typing import List, Optional


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
