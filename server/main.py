from fastapi import FastAPI, Depends

# from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base, get_api_key
from authentication.authentications import authentication_router
from workouts.workout import workout_router
from stripe_payments.payments import payments_router
from fastapi.middleware.cors import CORSMiddleware

# import models
import os


# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(debug=True, dependencies=[Depends(get_api_key)])
origins = [
    "http://localhost:5173",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
if os.getenv("ENABLE_PAYMENTS", "true") == "true":
    app.include_router(payments_router, prefix="/api/payment", tags=["Stripe Payments"])

if os.getenv("ENABLE_WORKOUT", "true") == "true":
    app.include_router(workout_router, prefix="/api/workout", tags=["Workouts"])


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
