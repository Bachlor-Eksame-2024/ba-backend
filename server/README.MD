# SETTING UP A SOA WITH SEPERATE SERVICES

The idea is to have the different usecases of the backend(fastAPI), running independently of each other.

Lets say we have 3 usecases, "Users", "Admins" and "Bookings".

All three of the usecase will be initiated from the main.py file, but they wont run inside the main.py file.
Instead we will create a folder for each usecase and create a usecase file inside that folder i.e. users.py or bookings.py

in the main.py file we will add the following:

`### Dynamically include routers based on environment variables or configuration
if os.getenv("ENABLE_USER_AUTH", "true") == "true":
    app.include_router(user_router, prefix="/auth", tags=["User Authentication"])

if os.getenv("ENABLE_BOOKING", "true") == "true":
    app.include_router(booking_router, prefix="/booking", tags=["Booking"])

if os.getenv("ENABLE_ADMINS", "true") == "true":
    app.include_router(admins_router, prefix="/admins", tags=["Admins"])`


By creating a separate router for each usecase we will have setup a SOA backend.

exsample setup in each usecase file.

`# user_auth.py
from fastapi import APIRouter
user_router = APIRouter()

@user_router.get("/login")
async def login():
    return {"message": "User login endpoint"}`

`# booking.py
from fastapi import APIRouter
booking_router = APIRouter()

@booking_router.get("/book")
async def book():
    return {"message": "Booking endpoint"}`

`# payments.py
from fastapi import APIRouter
payments_router = APIRouter()

@payments_router.get("/pay")
async def pay():
    return {"message": "Payments endpoint"}`