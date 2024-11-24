from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
import os

## Postgres Database URL
SQLALCHEMY_DATABASE_URL = os.getenv(
    ## DATABASE_URL is the default Postgres environment variable taken from docker-compose file
    ## the default value is "postgresql://postgres:postgres@postgres:5432/postgres"
    "DATABASE_URL",
    "postgresql://yourusername:yourpassword@postgres:5432/yourdatabase",
)

## use flush=True to force print to stdout immediately
## print(f"Using DATABASE_URL: {SQLALCHEMY_DATABASE_URL}", flush=True)

## Create a new engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


## Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


##### API ACCESS KEY #####
API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate API key"
        )
