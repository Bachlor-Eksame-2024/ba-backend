from pydantic import BaseModel


class BoksUpdate(BaseModel):
    user_id: str
    fitness_center_id: str
    boks_id: str
    boks_availability: str
