from fastapi import APIRouter, Depends, Query, Body, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from math import ceil
from database import get_db
from authentication.jwt import get_current_user
from models import Users, UserRoles, Bookings

admin_router = APIRouter(dependencies=[Depends(get_current_user)])


#######################
#### GET ALL USERS ####


@admin_router.get("/get-users")
def get_all_users(
    db: Session = Depends(get_db),
    fitness_center_id: int = Query(..., description="ID of the fitness center"),
    page: int = Query(default=1, gt=0),
    page_size: int = Query(default=10, gt=0),
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


@admin_router.get("/search-users")
def search_users(
    db: Session = Depends(get_db),
    fitness_center_id: int = Query(..., description="ID of the fitness center"),
    search_query: str = Query(..., min_length=1, description="Search query for users"),
    page: int = Query(default=1, gt=0),
    page_size: int = Query(default=10, gt=0),
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


###########################
#### UPDATE MEMBERSHIP ####
class MembershipUpdate(BaseModel):
    user_id: int
    is_member: bool


@admin_router.put("/update-membership")
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
@admin_router.delete("/delete-user/{user_id}")
def delete_user(
    user_id: int,
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


#######################
#### GET ALL BOKS ####
@admin_router.get("/get-boks")
def get_all_boks(
    db: Session = Depends(get_db),
    fitness_center_id: int = Query(..., description="ID of the fitness center"),
):
    boks = db.query(Users).filter(Users.fitness_center_fk == fitness_center_id).all()

    boks_list = [
        {
            "boks_id": boks.user_id,
            "first_name": boks.user_first_name,
            "last_name": boks.user_last_name,
            "email": boks.user_email,
            "phone": boks.user_phone,
            "is_member": boks.is_member,
            "role": boks.user_role,
        }
        for boks in boks
    ]

    return {"boks": boks_list}


###################
#### GET STATS ####


@admin_router.get("/get-stats")
def get_stats(
    db: Session = Depends(get_db),
    fitness_center_id: int = Query(..., description="ID of the fitness center"),
):
    # Get current date info
    today = datetime.now().date()
    first_day_of_month = today.replace(day=1)

    try:
        # New members this month (users created this month)
        new_members = (
            db.query(Users)
            .filter(
                Users.fitness_center_fk == fitness_center_id,
                Users.is_member == True,
                func.date(Users.created_at) >= first_day_of_month,
            )
            .count()
        )

        # New members today
        new_members_today = (
            db.query(Users)
            .filter(
                Users.fitness_center_fk == fitness_center_id,
                Users.is_member == True,
                func.date(Users.created_at) == today,
            )
            .count()
        )

        # Total members
        total_members = (
            db.query(Users)
            .filter(
                Users.fitness_center_fk == fitness_center_id, Users.is_member == True
            )
            .count()
        )

        # Total users (boks)
        total_boks = (
            db.query(Users).filter(Users.fitness_center_fk == fitness_center_id).count()
        )

        # Bookings checked in today
        boks_checked_in_today = (
            db.query(Bookings)
            .join(Users)
            .filter(
                Users.fitness_center_fk == fitness_center_id,
                func.date(Bookings.booking_date) == today,
            )
            .count()
        )

        # Bookings checked in this month
        boks_checked_in_month = (
            db.query(Bookings)
            .join(Users)
            .filter(
                Users.fitness_center_fk == fitness_center_id,
                func.date(Bookings.booking_date) >= first_day_of_month,
            )
            .count()
        )

        return {
            "new_members_month": new_members,
            "new_members_today": new_members_today,
            "total_members": total_members,
            "total_boks": total_boks,
            "checked_in_today": boks_checked_in_today,
            "checked_in_month": boks_checked_in_month,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")
