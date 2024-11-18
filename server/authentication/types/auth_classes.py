from pydantic import BaseModel


class User(BaseModel):
    user_id: str
    email: str
    password: str
    first_name: str
    last_name: str
    fitness_center_id: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str

class SignupUser(BaseModel):
    email: str
    password: str
    repeat_password: str
    first_name: str
    last_name: str
    fitness_center_id: str

class LoginUser(BaseModel):
    email: str
    password: str
    fitness_center_id: str