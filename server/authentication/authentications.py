from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import timedelta
from .jwt import create_access_token, get_current_user
from authentication.types.auth_classes import SignupUser, LoginUser
from database import get_db
from models import User

authentication_router = APIRouter()
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


#####
##### Login Endpoint #####
@authentication_router.post("/login")
async def login(user: LoginUser):

    ## compare the password with the hashed password
    # pwd_context.verify(plain_password, hashed_password)

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


#####
##### Signup Endpoint #####
@authentication_router.post("/signup")
async def signup(user: SignupUser):
    hash_password = pwd_context.hash(user.password)
    user_info = {
        "email": user.email,
        "password": hash_password,
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


#####
##### Log out Endpoint #####
@authentication_router.get("/logout")  # , response_model=Token)
async def logout(request: Request):
    user = await get_current_user(request)
    print({"current_user": user}, flush=True)
    response = JSONResponse({"message": "User logged out"}, status_code=200)
    response.delete_cookie(key="fitboks-auth-Token")
    return response


#####
##### Verify User login Endpoint #####
@authentication_router.get("/verify-login")  # , response_model=Token)
async def verify_Login(current_user: dict = Depends(get_current_user)):
    if current_user:
        response = JSONResponse(
            {"message": "User is logged in", "user": current_user["user_info"]},
            status_code=200,
        )
    return response


#####
##### Change Password Endpoint #####
@authentication_router.post("/change-password")
async def change_password(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
):
    
    # Get all the users from the database
    db_users = db.query(User).all()
    # Print the users to the console
    for user in db_users:
        print(user.__dict__, flush=True)


    # Get the user info from the current_user
    # Get the new password and the old password from the request
    # Compare the old password with the hashed password
    # Hash the new password
    # Update the password with the new password

    return "Change Password"
