from fastapi import HTTPException, status, Request
import jwt
from jwt import PyJWTError
from datetime import datetime, timedelta, timezone
from typing import Union
import json

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"


## Function til at lave et access token med en expiration time
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire, "sub": json.dumps(data)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


## Function til at hente den nuværende bruger fra JWT token
async def get_current_user(request: Request):
    print("Headers:", dict(request.headers))  # Debug headers
    print("All Cookies:", request.cookies)  # Debug cookies
    token = request.cookies.get("fitboks-auth-Token")
    print("Auth Token Found:", bool(token))
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Payload: {payload}", flush=True)
        user_info = json.loads(payload.get("sub"))
        if user_info is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except PyJWTError as e:
        print(f"JWTError: {e}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"user_info": user_info}
