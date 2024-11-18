from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone

## this file contains the database models
## each model is a class that inherits from Base
## Base is a declarative_base instance from SQLAlchemy
## it is used to create the database tables


## User model - represents the users table in the database boksfit
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    fitness_center_id = Column(Integer, ForeignKey("fitness_centers.fitness_center_id"))
    role = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationship example
    items = relationship("Item", back_populates="owner")
