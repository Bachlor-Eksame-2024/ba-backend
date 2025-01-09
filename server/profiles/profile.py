from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from fastapi_csrf_protect import CsrfProtect
from sqlalchemy import func
from passlib.context import CryptContext
from database import get_db
from authentication.jwt import get_current_user, create_access_token
from datetime import datetime, timezone, timedelta
from models import Users, Bookings
from profiles.types.profile_types import (
    ChangePassword,
    UpdateProfile,
    UserStatsResponse,
    UserRoleUpdate,
)
from authentication.validate import (
    validate_password,
    valide_email,
    validate_first_name,
    validate_last_name,
    validate_phone_number,
)
import logging, json

profile_router = APIRouter(
    dependencies=[Depends(get_current_user)]
)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ACCESS_TOKEN_EXPIRE_MINUTES = 180
#########################
#### Change password ####


@profile_router.put("/change-password/")
async def change_password(
    user: ChangePassword,
    db: Session = Depends(get_db),
):

    # Get all the users from the database
    get_user_in_db = db.query(Users).filter(Users.user_id == user.user_id).first()
    # Print the users to the console
    if not pwd_context.verify(user.old_password, get_user_in_db.password_hash):
        raise HTTPException(status_code=400, detail="Invalid Password")

    if not user.new_password == user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    if not validate_password(user.new_password):
        raise HTTPException(
            status_code=400,
            detail="""Invalid password most contain at least 8 characters and
            1 number and 1 special character""",
        )
    print(get_current_user, flush=True)

    hash_password = pwd_context.hash(user.new_password)
    # Get current timestamp
    current_time = datetime.now(timezone.utc)
    # Update the user password
    # Update the user password and updated_at fields
    get_user_in_db.password_hash = hash_password
    get_user_in_db.updated_at = current_time

    # Commit changes to the database
    db.commit()

    return {"message": "Password updated successfully"}


@profile_router.put("/update-profile")
async def update_profile(
    user: UpdateProfile,
    db: Session = Depends(get_db),
):
    # Get all the users from the database
    get_user_in_db = db.query(Users).filter(Users.user_id == user.user_id).first()

    # Update the user profile
    if not validate_first_name(user.first_name):
        raise HTTPException(status_code=400, detail="Ugyldigt fornavn")
    if not validate_last_name(user.last_name):
        raise HTTPException(status_code=400, detail="Ugyldigt efternavn")
    if not valide_email(user.email):
        raise HTTPException(status_code=400, detail="Ugyldigt Email")
    if not validate_phone_number(user.phone):
        raise HTTPException(status_code=400, detail="Ugyldigt Telefonnummer")

    # Check email only if it changed
    if user.email.lower() != get_user_in_db.user_email.lower():
        user_email_exists = (
            db.query(Users)
            .filter(func.lower(Users.user_email) == user.email.lower())
            .first()
        )
        if user_email_exists:
            raise HTTPException(
                status_code=400, detail="Bruger-e-mail eksisterer allerede"
            )

    # Check phone only if it changed
    if user.phone != get_user_in_db.user_phone:
        user_phone_exists = (
            db.query(Users).filter(Users.user_phone == user.phone).first()
        )
        if user_phone_exists:
            raise HTTPException(
                status_code=400, detail="Telefonnummer eksisterer allerede"
            )

    # Get current timestamp
    current_time = datetime.now(timezone.utc)

    get_user_in_db.user_first_name = user.first_name
    get_user_in_db.user_last_name = user.last_name
    get_user_in_db.user_email = user.email
    get_user_in_db.user_phone = user.phone
    get_user_in_db.fitness_center_fk = user.fitness_center_id
    get_user_in_db.updated_at = current_time

    db.commit()
    # Refresh the instance to get the updated values
    db.refresh(get_user_in_db)

    # Return the updated user profile
    updated_user = {
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

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": updated_user}, expires_delta=access_token_expires
    )

    response = JSONResponse(
        {"user": updated_user, "message": "Profile updated successfully"},
        status_code=201,
    )
    response.set_cookie(
        key="fitboks-auth-Token",
        value=access_token,
        httponly=True,
        samesite="Strict",
        secure=True,
    )

    return {"message": "Profile updated successfully", "user": updated_user}


# user-stats/{id}, response_model=userStatsResponse
@profile_router.get("/user-stats/{user}", response_model=UserStatsResponse)
def get_user_stats(
    user: str = Path(..., description="The ID of the user"),
    db: Session = Depends(get_db),
):
    today = datetime.now()
    start_month = (today.replace(day=1) - timedelta(days=330)).replace(day=1)

    monthly_bookings = {}
    weekly_bookings = {}

    # Generate months
    current = start_month
    while current <= today:
        month_key = current.strftime("%Y-%m")
        monthly_bookings[month_key] = 0
        current = (current.replace(day=1) + timedelta(days=32)).replace(day=1)

    # Generate exactly 4 weeks
    for week_num in range(4):
        week_date = today - timedelta(weeks=week_num)
        week_key = week_date.strftime("%Y-%U")
        weekly_bookings[week_key] = 0

    # Get bookings
    get_user_bookings = (
        db.query(Bookings)
        .filter(
            Bookings.user_id == user,
            func.date(Bookings.booking_date) >= start_month,
        )
        .order_by(Bookings.booking_date.desc())
        .all()
    )

    # Update counts
    for booking in get_user_bookings:
        month_key = booking.booking_date.strftime("%Y-%m")
        week_key = booking.booking_date.strftime("%Y-%U")
        if month_key in monthly_bookings:
            monthly_bookings[month_key] += 1
        if week_key in weekly_bookings:
            weekly_bookings[week_key] += 1

    # Format monthly stats with 3-letter abbreviations
    monthly_stats = [
        {
            "pv": value,
            "name": datetime.strptime(key, "%Y-%m").strftime("%b"),
        }
        for key, value in sorted(monthly_bookings.items(), reverse=True)
    ]

    # Format weekly stats with simple week numbers 1-4
    weekly_stats = [
        {"pv": value, "name": f"Uge {4 - idx}"}
        for idx, (key, value) in enumerate(
            sorted(weekly_bookings.items(), reverse=True)
        )
    ]

    return {
        "total_bookings": len(get_user_bookings) if get_user_bookings else 0,
        "monthly_stats": monthly_stats[::-1],
        "weekly_stats": weekly_stats[::-1],
    }


@profile_router.post("/change-user-role")
async def change_user_role(
    request: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:

        # Get user to update
        user = db.query(Users).filter(Users.user_id == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Toggle role between admin (1) and user (2)
        new_role = 2 if user.user_role_fk == 1 else 1
        user.user_role_fk = new_role

        db.commit()

        return {
            "status": "success",
            "message": f"User role changed to {'admin' if new_role == 1 else 'user'}",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
