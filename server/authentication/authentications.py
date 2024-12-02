from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from .jwt import create_access_token, get_current_user
from authentication.types.auth_classes import SignupUser, LoginUser
from authentication.validate import (
    validate_password,
    valide_email,
    validate_first_name,
    validate_last_name,
    validate_phone_number,
)
from authentication.mail import (
    generate_verification_token,
    send_verification_email,
)
from database import get_db
from models import Users

authentication_router = APIRouter()
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


#####
##### Login Endpoint #####
@authentication_router.post("/login")
async def login(user: LoginUser, db: Session = Depends(get_db)):
    # Get the user from the database
    get_user_in_db = db.query(Users).filter(Users.user_email == user.email).first()
    if not get_user_in_db:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Check if the password is correct
    if not pwd_context.verify(user.password, get_user_in_db.password_hash):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Create user info dict from saved user
    user_info = {
        "email": get_user_in_db.user_email,
        "first_name": get_user_in_db.user_first_name,
        "last_name": get_user_in_db.user_last_name,
        "user_phone": get_user_in_db.user_phone,
        "fitness_center": get_user_in_db.fitness_center.fitness_center_name,
        "user_id": get_user_in_db.user_id,
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
##### SIGN UP #####
@authentication_router.post("/signup")
async def signup(user: SignupUser, db: Session = Depends(get_db)):
    # Check if user with email already exists
    user_email_exists = db.query(Users).filter(Users.user_email == user.email).first()
    if user_email_exists:
        raise HTTPException(status_code=400, detail="User email already exists")
    # Check if user with Phone number already exists
    user_phone_exists = db.query(Users).filter(Users.user_phone == user.phone).first()
    if user_phone_exists:
        raise HTTPException(status_code=400, detail="User phone number already exists")
    # Validate Email
    if not valide_email(user.email):
        raise HTTPException(status_code=400, detail="Invalid email")
    # Validate Phone number
    if not validate_phone_number(user.phone):
        raise HTTPException(status_code=400, detail="Invalid phone number")
    # Validate Password
    if not validate_password(user.password):
        raise HTTPException(status_code=400, detail="Invalid password")
    # Validate First Name
    if not validate_first_name(user.first_name):
        raise HTTPException(status_code=400, detail="Invalid first name")
    # Validate Last Name
    if not validate_last_name(user.last_name):
        raise HTTPException(status_code=400, detail="Invalid last name")

    # Hash password
    hash_password = pwd_context.hash(user.password)
    # Get current timestamp
    current_time = datetime.now(timezone.utc)
    # Create new user model instance with all required fields
    # Generate verification token
    verification_token = generate_verification_token()

    new_user = Users(
        user_email=user.email,
        password_hash=hash_password,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        fitness_center_fk=user.fitness_center_id,
        user_role_fk=1,  # Assuming default role id is 1
        is_member=True,
        is_verified=False,
        verification_token=verification_token,
        created_at=current_time,
        updated_at=current_time,
        user_phone=user.phone,  # Ensure `phone` is a field in `SignupUser`
    )
    # Add and commit to database
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        print(f"Error creating user: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail="Error creating user")
    # Create user info dict from saved user
    user_info = {
        "email": new_user.user_email,
        "first_name": new_user.user_first_name,
        "last_name": new_user.user_last_name,
        "user_phone": new_user.user_phone,
        "fitness_center": new_user.fitness_center.fitness_center_name,
        "is_verified": new_user.is_verified,
        "user_id": new_user.user_id,
    }
    # If user has a user_id, send verification email
    if new_user.user_id:
        # Send verification email
        email_sent = await send_verification_email(
            email=new_user.user_email, verification_token=verification_token
        )
        if not email_sent:
            # Optionally handle email sending failure
            print("Failed to send verification email")

    # Generate JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_info}, expires_delta=access_token_expires
    )

    # Create response
    response = JSONResponse({"user": user_info}, status_code=201)
    response.set_cookie(
        key="fitboks-auth-Token",
        value=access_token,
        httponly=True,
        samesite="Strict",
        secure=True,
    )
    return response


#####
##### VERIFY USER EMAIL #####
@authentication_router.get("/verify-email")
async def verify_email(
    token: str,
    email: str,
    db: Session = Depends(get_db),  # You'll need to implement this dependency
):
    # Find user by email and token
    user = (
        db.query(Users)
        .filter(Users.user_email == email, Users.verification_token == token)
        .first()
    )

    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    # Mark user as verified
    user.is_verified = True
    user.verification_token = None
    db.commit()

    return {"message": "Email verified successfully"}

  
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # Get all the users from the database
    db_users = db.query(Users).all()
    # Print the users to the console
    for user in db_users:
        print(user.__dict__, flush=True)

    # Get the user info from the current_user
    # Get the new password and the old password from the request
    # Compare the old password with the hashed password
    # Hash the new password
    # Update the password with the new password

    return "Change Password"
