from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


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


app = FastAPI(debug=True)

origins = [
    "http://localhost:5173",
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    "https://jonathan.fitboks.dk",  # Jonathan
    "https://asger.fitboks.dk",  # Asger
    "https://mille.fitboks.dk",  # Mille
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-CSRF-Token"], 
    expose_headers=["Set-Cookie", "X-CSRF-Token"],
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
        authentication_router,
        prefix="/api/auth",
        tags=["User Authentication"],dependencies=[Depends(get_api_key)])

if os.getenv("ENABLE_BOOKING", "true") == "true":
    app.include_router(
        booking_router,
        prefix="/api/booking",
        tags=["Booking Request"],
        dependencies=[Depends(get_api_key)],
    )

if os.getenv("ENABLE_PAYMENTS", "true") == "true":
    app.include_router(
        payments_router,
        prefix="/api/payment",
        tags=["Stripe Payments"])

if os.getenv("ENABLE_WORKOUT", "true") == "true":
    app.include_router(
        workout_router,
        prefix="/api/workout",
        tags=["Workouts"],
        dependencies=[Depends(get_api_key)],
    )

if os.getenv("ENABLE_ADMIN", "true") == "true":
    app.include_router(
        admin_router,
        prefix="/api/admin",
        tags=["Admin Requests"],
        dependencies=[Depends(get_api_key)],
    )

if os.getenv("ENABLE_PROFILE", "true") == "true":
    app.include_router(
        profile_router,
        prefix="/api/profile",
        tags=["Profile Changes"],
        dependencies=[Depends(get_api_key)],
    )

# Add the seed router to the app
app.include_router(
    seed_router,
    prefix="/api/seed",
    tags=["Database Seeding"])


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
