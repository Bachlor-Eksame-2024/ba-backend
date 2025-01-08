from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi_csrf_protect import CsrfProtect
from passlib.context import CryptContext
from sqlalchemy import func
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
ACCESS_TOKEN_EXPIRE_MINUTES = 180
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


#####
##### Login Endpoint #####
@authentication_router.post("/login")
async def login(
    user: LoginUser,
    db: Session = Depends(get_db)
):
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
        "fitness_center_id": get_user_in_db.fitness_center.fitness_center_id,
        "is_member": get_user_in_db.is_member,
        "is_verified": get_user_in_db.is_verified,
        "user_role": get_user_in_db.user_role_fk,
        "user_role_name": get_user_in_db.user_role.role_name,
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
        samesite="Strict",  # Changed from "None" to "Lax"
        secure=True,  # This should be True in production with HTTPS
        path="/",
    )
    ## return the response with the JWT token
    return response


#####
##### SIGN UP #####
@authentication_router.post("/signup")
async def signup(
    user: SignupUser,
    db: Session = Depends(get_db),
):
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

    # Check if user with email already exists
    user_email_exists = (
        db.query(Users)
        .filter(func.lower(Users.user_email) == user.email.lower())
        .first()
    )
    if user_email_exists:
        raise HTTPException(status_code=400, detail="User email already exists")
    # Check if user with Phone number already exists
    user_phone_exists = db.query(Users).filter(Users.user_phone == user.phone).first()
    if user_phone_exists:
        raise HTTPException(status_code=400, detail="User phone number already exists")

    # Hash password
    hash_password = pwd_context.hash(user.password)
    # Get current timestamp
    current_time = datetime.now(timezone.utc)
    # Create new user model instance with all required fields
    # Generate verification token
    verification_token = generate_verification_token()

    new_user = Users(
        user_email=user.email.lower(),
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
    try:
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
            "fitness_center_id": new_user.fitness_center.fitness_center_id,
            "is_member": new_user.is_member,
            "is_verified": new_user.is_verified,
            "user_role": new_user.user_role_fk,
            "user_role_name": new_user.user_role.role_name,
            "user_id": new_user.user_id,
        }

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
        # Try to send email in background
        if new_user.user_id:
            try:
                print(f"Attempting to send verification email to {new_user.user_email}")
                email_sent = await send_verification_email(
                    email=new_user.user_email, verification_token=verification_token
                )
                print(f"Email sent status: {email_sent}")
            except Exception as e:
                print(f"Failed to send verification email: {e}")
                # Don't block the response, just log the error
                pass

        return response

    except Exception as e:
        print(f"Signup error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


#####
##### VERIFY USER EMAIL #####
@authentication_router.get("/verify-email")
async def verify_email(
    token: str,
    email: str,
    db: Session = Depends(get_db),
):
    try:
        # Log received values for debugging
        print(f"Verifying email: {email} with token: {token}")

        # Find user by email and token
        user = (
            db.query(Users)
            .filter(
                Users.user_email == email,
                Users.verification_token == token,
                Users.is_verified == False,  # Only verify unverified users
            )
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=404, detail="Invalid verification token or email"
            )

        # Mark user as verified
        user.is_verified = True
        user.verification_token = None
        user.updated_at = datetime.now()
        db.commit()
        return {"message": "Email verified successfully", "user_email": user.user_email}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


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
@authentication_router.get("/verify-login")
async def verify_login(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    try:
        user_info = current_user.get("user_info", {}).get("sub", {})

        return {"user": user_info}
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))
