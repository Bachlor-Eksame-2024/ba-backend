from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from pydantic import BaseModel
import secrets
# rate limit
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
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

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(debug=True, dependencies=[Depends(get_api_key)])
# Add rate limit middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

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
        authentication_router,
        prefix="/api/auth",
        tags=["User Authentication"],
        # Rate limit to 30 requests per minute
        dependencies=[Depends(limiter.limit("30/minute"))],
    )

if os.getenv("ENABLE_BOOKING", "true") == "true":
    app.include_router(
        booking_router,
        prefix="/api/booking",
        tags=["Booking Request"],
        # Rate limit to 60 requests per minute
        dependencies=[Depends(limiter.limit("60/minute"))],
    )

if os.getenv("ENABLE_PAYMENTS", "true") == "true":
    app.include_router(
        payments_router,
        prefix="/api/payment",
        tags=["Stripe Payments"],
        dependencies=[Depends(limiter.limit("60/minute"))],
    )

if os.getenv("ENABLE_WORKOUT", "true") == "true":
    app.include_router(
        workout_router,
        prefix="/api/workout",
        tags=["Workouts"],
        dependencies=[Depends(limiter.limit("60/minute"))],
    )

if os.getenv("ENABLE_ADMIN", "true") == "true":
    app.include_router(
        admin_router,
        prefix="/api/admin",
        tags=["Admin Requests"],
        dependencies=[Depends(limiter.limit("60/minute"))],
    )

if os.getenv("ENABLE_PROFILE", "true") == "true":
    app.include_router(
        profile_router,
        prefix="/api/profile",
        tags=["Profile Changes"],
        dependencies=[Depends(limiter.limit("60/minute"))],
    )

# Add the seed router to the app
app.include_router(
    seed_router,
    prefix="/api/seed",
    tags=["Database Seeding"],
    dependencies=[Depends(limiter.limit("60/minute"))],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
