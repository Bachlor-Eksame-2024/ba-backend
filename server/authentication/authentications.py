from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone
from .jwt import create_access_token, get_current_user
from authentication.types.auth_classes import SignupUser, LoginUser

authentication_router = APIRouter()
ACCESS_TOKEN_EXPIRE_MINUTES = 30


############################################
##### Login Endpoint #####
@authentication_router.post("/login")
async def login(user: LoginUser):
    user_info = {
        "email": user.email,
        "first_name": "Jaime",
        "first_last": "Lannister",
        "fitness_center_id": user.fitness_center_id,
        "user_id": "A random user id",
    }
    ## JWT token creation
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_info}, expires_delta=access_token_expires
    )
    response = JSONResponse({"user": user_info}, status_code=200)
    response.set_cookie(
        key="fitboks-auth-Token",
        value=access_token,
        httponly=True,
        samesite="Strict",
        secure=True,
    )
    ## return the response with the JWT token
    return response


############################################
##### Signup Endpoint #####
@authentication_router.post("/signup")
async def signup(user: SignupUser):

    user_info = {
        "email": user.email,
        "first_name": user.first_name,
        "first_last": user.last_name,
        "fitness_center_id": user.fitness_center_id,
        "user_id": "A random user id",
    }
    ## JWT token creation
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_info}, expires_delta=access_token_expires
    )
    response = JSONResponse({"user": user_info}, status_code=200)
    response.set_cookie(
        key="fitboks-auth-Token",
        value=access_token,
        httponly=True,
        samesite="Strict",
        secure=True,
    )
    ## return the response with the JWT token
    return response


############################################
##### Log out Endpoint #####
@authentication_router.get("/logout")  # , response_model=Token)
async def logout(request: Request):
    user = await get_current_user(request)
    print({"current_user": user}, flush=True)
    response = JSONResponse({"message": "User logged out"}, status_code=200)
    response.delete_cookie(key="fitboks-auth-Token")
    return response


############################################
##### Verify User login Endpoint #####
@authentication_router.get("/verify-login")  # , response_model=Token)
async def verify_Login(current_user: dict = Depends(get_current_user)):
    if current_user:
        response = JSONResponse(
            {"message": "User is logged in", "user": current_user["user_info"]},
            status_code=200,
        )
    return response
