from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from pydantic import BaseModel
import secrets
# from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base, get_api_key
from authentication.authentications import authentication_router
from workouts.workout import workout_router
from admin.admin import admin_router
from stripe_payments.payments import payments_router
from profiles.profile import profile_router
from seed_data import seed_router
from bookings.bookings import booking_router

# import models
import os


# Create database tables
Base.metadata.create_all(bind=engine)


# Add CSRF Settings
class CsrfSettings(BaseModel):
    secret_key: str = os.getenv("CSRF_SECRET_KEY")
    token_expires_minutes: int = 180


@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()


app = FastAPI(debug=True, dependencies=[Depends(get_api_key)])

origins = [
    "http://localhost:5173",
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://159.223.238.147",  # Jonathan
    "http://164.92.227.113",  # Asger
    "http://104.248.40.117"  # Mille
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-CSRF-Token"], 
    expose_headers=["Set-Cookie", "X-CSRF-Token"],
)


@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    return JSONResponse(
        status_code=403, content={"detail": "CSRF token missing or invalid"}
    )


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if os.getenv("ENABLE_USER_AUTH", "true") == "true":
    app.include_router(
        authentication_router, prefix="/api/auth", tags=["User Authentication"]
    )

if os.getenv("ENABLE_BOOKING", "true") == "true":
    app.include_router(booking_router, prefix="/api/booking", tags=["Booking Request"])

if os.getenv("ENABLE_PAYMENTS", "true") == "true":
    app.include_router(payments_router, prefix="/api/payment", tags=["Stripe Payments"])

if os.getenv("ENABLE_WORKOUT", "true") == "true":
    app.include_router(workout_router, prefix="/api/workout", tags=["Workouts"])

if os.getenv("ENABLE_ADMIN", "true") == "true":
    app.include_router(admin_router, prefix="/api/admin", tags=["Admin Requests"])

if os.getenv("ENABLE_PROFILE", "true") == "true":
    app.include_router(profile_router, prefix="/api/profile", tags=["Profile Changes"])

# Add the seed router to the app
app.include_router(seed_router, prefix="/api/seed", tags=["Database Seeding"])


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
