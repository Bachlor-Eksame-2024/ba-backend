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


