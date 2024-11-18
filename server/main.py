from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from authentication.authentications import authentication_router
import models
import os


# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(debug=True)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if os.getenv("ENABLE_USER_AUTH", "true") == "true":
    app.include_router(authentication_router, prefix="/api/auth", tags=["User Authentication"])


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
