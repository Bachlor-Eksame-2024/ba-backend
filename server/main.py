from fastapi import FastAPI

# from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from authentication.authentications import authentication_router
from fastapi.middleware.cors import CORSMiddleware
import models
import os


# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(debug=True)
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


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
