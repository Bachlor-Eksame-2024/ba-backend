from fastapi import APIRouter, Depends, Path, Body, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from math import ceil
from database import get_db
from authentication.jwt import get_current_user
from models import Users, UserRoles, Bookings
from admin.types.admin_types import UsersResponse

from .admin_boxes import boxes_router
from .admin_stats import stats_router

admin_router = APIRouter(
    dependencies=[Depends(get_current_user)]
)
admin_router.include_router(boxes_router)
admin_router.include_router(stats_router)


#######################
#### GET ALL USERS ####


@admin_router.get(
    "/users/{fitness_center_id}/{page}/{page_size}",
    response_model=UsersResponse,
)
def get_all_users(
    db: Session = Depends(get_db),
    fitness_center_id: int = Path(..., description="ID of the fitness center"),
    page: int = Path(..., description="Page number", gt=0),
    page_size: int = Path(..., description="Number of items per page", gt=0),
):
    skip = (page - 1) * page_size

    # Get total count of filtered users
    total_users = (
        db.query(Users).filter(Users.fitness_center_fk == fitness_center_id).count()
    )

    # Get specific user fields with join to get role name
    users = (
        db.query(
            Users.user_id,
            Users.user_first_name,
            Users.user_last_name,
            Users.user_email,
            Users.user_phone,
            Users.is_member,
            UserRoles.role_name.label("user_role"),
        )
        .join(UserRoles)
        .filter(Users.fitness_center_fk == fitness_center_id)
        .offset(skip)
        .limit(page_size)
        .all()
    )

    # Convert SQLAlchemy result to dict
    users_list = [
        {
            "user_id": user.user_id,
            "first_name": user.user_first_name,
            "last_name": user.user_last_name,
            "email": user.user_email,
            "phone": user.user_phone,
            "is_member": user.is_member,
            "role": user.user_role,
        }
        for user in users
    ]

    return {
        "users": users_list,
        "total": total_users,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total_users / page_size),
    }


######################
#### SEARCH USERS ####


@admin_router.get(
    "/search-users/{fitness_center_id}/{page}/{page_size}/{search_query}",
    response_model=UsersResponse,
)
def search_users(
    db: Session = Depends(get_db),
    fitness_center_id: int = Path(..., description="ID of the fitness center"),
    search_query: str = Path(..., min_length=1, description="Search query for users"),
    page: int = Path(..., description="Page number", gt=0),
    page_size: int = Path(..., description="Number of items per page", gt=0),
):
    skip = (page - 1) * page_size
    search_term = f"%{search_query.strip()}%"

    # Build base query with specific fields
    base_query = db.query(
        Users.user_id,
        Users.user_first_name,
        Users.user_last_name,
        Users.user_email,
        Users.user_phone,
        Users.is_member,
        UserRoles.role_name.label("user_role"),
    ).join(UserRoles)

    # Simplified search filter
    search_filter = (
        Users.user_first_name.ilike(search_term)
        | Users.user_last_name.ilike(search_term)
        | Users.user_email.ilike(search_term)
        | Users.user_phone.ilike(search_term)
    )

    filtered_query = base_query.filter(
        Users.fitness_center_fk == fitness_center_id, search_filter
    )

    # Get total count for pagination
    total_users = filtered_query.count()

    # Get paginated results
    users = filtered_query.offset(skip).limit(page_size).all()

    # Convert to list of dicts
    users_list = [
        {
            "user_id": user.user_id,
            "first_name": user.user_first_name,
            "last_name": user.user_last_name,
            "email": user.user_email,
            "phone": user.user_phone,
            "is_member": user.is_member,
            "role": user.user_role,
        }
        for user in users
    ]
    print(filtered_query.statement)
    return {
        "users": users_list,
        "total": total_users,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total_users / page_size),
    }


@admin_router.get("/booking/{booking_id}")
def get_booking_by_id(
    booking_id: int,
    db: Session = Depends(get_db),
):
    booking = (
        db.query(Bookings)
        .join(Users, Users.user_id == Bookings.user_id)
        .filter(Bookings.booking_id == booking_id)
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    return {
        "booking_id": booking.booking_id,
        "user_id": booking.user_id,
        "booking_box_id_fk": booking.booking_box_id_fk,
        "booking_date": booking.booking_date.strftime("%Y-%m-%d %H:%M:%S"),
        "booking_code": booking.booking_code,
        "booking_start_hour": booking.booking_start_hour,
        "booking_duration_hours": booking.booking_duration_hours,
        "booking_end_hour": booking.booking_end_hour,
        "booking_timestamp": booking.booking_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "user_email": booking.user.user_email,
        "user_first_name": booking.user.user_first_name,
        "user_last_name": booking.user.user_last_name,
        "user_phone": booking.user.user_phone,
    }


###########################
#### UPDATE MEMBERSHIP ####
class MembershipUpdate(BaseModel):
    user_id: int
    is_member: bool


@admin_router.put("/membership")
def update_membership(
    data: MembershipUpdate = Body(...), db: Session = Depends(get_db)
):
    user = db.query(Users).filter(Users.user_id == data.user_id).first()
    if not user:
        return {"error": "User not found"}

    user.is_member = data.is_member
    db.commit()
    return {"message": "Membership status updated successfully"}


######################
#### DELETE USER ####
@admin_router.delete("/user/{user_id}")
def delete_user(
    user_id: int = Path(..., description="ID of the user to delete"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Find user
    user = db.query(Users).filter(Users.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Verify user belongs to same fitness center as admin
    if user.fitness_center_fk != current_user.get("fitness_center_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete user from different fitness center",
        )

    db.delete(user)
    db.commit()

    return {"status": "success", "message": "User deleted successfully"}
