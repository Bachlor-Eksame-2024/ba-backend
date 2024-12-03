from fastapi import APIRouter, Depends, Query, Body, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from collections import defaultdict
from math import ceil
from database import get_db
from authentication.jwt import get_current_user
from models import Users, UserRoles, Bookings, Boxes

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
    boks = db.query(Boxes).filter(Boxes.fitness_center_fk == fitness_center_id).all()

    """ boks_list = [
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
    ] """

    return {"boks": boks}


#######################
#### GET ALL BOKS ####


@admin_router.get("/get-boks-avaliability-by-id")
def get_boks_avaliability_by_id(
    db: Session = Depends(get_db),
    fitness_center_id: int = Query(..., description="ID of the fitness center"),
    boks_id: int = Query(..., description="ID of the boks"),
):
    try:
        # Get current date and date range
        today = datetime.now().date()
        date_range = [today + timedelta(days=x) for x in range(7)]

        # Get box
        box = (
            db.query(Boxes)
            .filter(
                Boxes.fitness_center_fk == fitness_center_id, Boxes.box_id == boks_id
            )
            .first()
        )

        if not box:
            raise HTTPException(status_code=404, detail="Box not found")

        # Get all bookings for this box in next 7 days
        bookings = (
            db.query(Bookings)
            .filter(
                Bookings.booking_box_id_fk == boks_id,
                func.date(Bookings.booking_date) >= today,
                func.date(Bookings.booking_date) <= date_range[-1],
            )
            .all()
        )

        # Create availability map
        availability = {}
        for date in date_range:
            availability[date.strftime("%Y-%m-%d")] = {
                hour: {"available": True, "booking": None} for hour in range(24)
            }

        # Mark booked hours
        for booking in bookings:
            booking_date = booking.booking_date.strftime("%Y-%m-%d")
            if booking_date in availability:
                for hour in range(
                    booking.booking_start_hour,
                    booking.booking_start_hour + booking.booking_duration_hours,
                ):
                    if hour < 24:  # Don't exceed day boundary
                        availability[booking_date][hour] = {
                            "available": False,
                            "booking": {
                                "booking_id": booking.booking_id,
                                "start_hour": booking.booking_start_hour,
                                "duration": booking.booking_duration_hours,
                                "end_hour": booking.booking_start_hour
                                + booking.booking_duration_hours,
                            },
                        }

        return {"box_id": box.box_id, "dates": availability}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching availability: {str(e)}"
        )


###########################
#### GET BOOKING BY ID ####

@admin_router.get("/get-booking-by-id")
def get_booking_by_id(
    db: Session = Depends(get_db),
    booking_id: int = Query(..., description="ID of the booking"),
):
    booking = db.query(Bookings).filter(Bookings.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    return {
        "booking_id": booking.booking_id,
        "user_id": booking.user_id,
        "user_first_name": booking.user.user_first_name,
        "user_last_name": booking.user.user_last_name,
        "fitness_center_id": booking.user.fitness_center_fk,
        "fitness_center_name": booking.user.fitness_center.fitness_center_name,
        "box_id": booking.booking_box_id_fk,
        "booking_date": booking.booking_date,
        "booking_code": booking.booking_code,
        "start_hour": booking.booking_start_hour,
        "duration_hours": booking.booking_duration_hours,
        "end_hour": booking.booking_start_hour + booking.booking_duration_hours,
    }



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

        # Total Fitness Center boxes (boks)
        total_boks = (
            db.query(Boxes).filter(Boxes.fitness_center_fk == fitness_center_id).count()
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

        # Get date range
        today = datetime.now().date()
        thirty_days_ago = today - timedelta(days=30)

        # Get bookings grouped by date
        daily_bookings = (
            db.query(
                func.date(Bookings.booking_date).label("date"),
                func.count().label("count"),
            )
            .join(Users)
            .filter(
                Users.fitness_center_fk == fitness_center_id,
                func.date(Bookings.booking_date) >= thirty_days_ago,
                func.date(Bookings.booking_date) <= today,
            )
            .group_by(func.date(Bookings.booking_date))
            .all()
        )

        # Create dict with all dates initialized to 0
        booking_dict = defaultdict(int)
        current_date = thirty_days_ago
        while current_date <= today:
            booking_dict[current_date.strftime("%Y-%m-%d")] = 0
            current_date += timedelta(days=1)

        # Fill in actual booking counts
        for date, count in daily_bookings:
            booking_dict[date.strftime("%Y-%m-%d")] = count

        # Convert to array of objects
        daily_stats = [
            {"date": date, "count": count} for date, count in booking_dict.items()
        ]

        return {
            "new_members_month": new_members,
            "new_members_today": new_members_today,
            "total_members": total_members,
            "total_boks": total_boks,
            "checked_in_today": boks_checked_in_today,
            "daily_bookings": daily_stats,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


##############################
#### GET BOX AVALIABLILTY ####


def does_time_overlap(start1: int, end1: int, start2: int, end2: int) -> bool:
    """Check if two time periods overlap"""
    return not (end1 <= start2 or start1 >= end2)


@admin_router.get("/get-box-availability")
def get_box_availability(
    db: Session = Depends(get_db),
    fitness_center_id: int = Query(..., description="ID of the fitness center"),
    date: datetime = Query(..., description="Date to check availability"),
    current_time: str = Query(..., description="Current time in HH:mm format"),
    duration: int = Query(..., ge=1, le=4, description="Duration in hours (1-4)"),
):
    try:
        # Parse current time and get next available hour
        current_hour = datetime.strptime(current_time, "%H:%M").hour
        next_available_hour = current_hour + 1 if current_hour < 23 else None

        if next_available_hour is None:
            return {"message": "No more bookings available today"}

        # Get all boxes for the fitness center
        boxes = (
            db.query(Boxes).filter(Boxes.fitness_center_fk == fitness_center_id).all()
        )

        # Get existing bookings for the date
        bookings = (
            db.query(Bookings)
            .filter(
                Bookings.booking_box_id_fk.in_([box.box_id for box in boxes]),
                func.date(Bookings.booking_date) == date.date(),
            )
            .all()
        )

        availability = {}
        for box in boxes:
            availability[box.box_id] = []

            # Check each possible starting hour
            for start_hour in range(next_available_hour, 24 - duration + 1):
                end_hour = start_hour + duration
                is_available = True

                # Check against all existing bookings
                for booking in bookings:
                    if booking.booking_box_id_fk == box.box_id:
                        if does_time_overlap(
                            start_hour,
                            end_hour,
                            booking.booking_start_hour,
                            booking.booking_start_hour + booking.booking_duration_hours,
                        ):
                            is_available = False
                            break

                if is_available:
                    availability[box.box_id].append(
                        {"start_hour": start_hour, "end_hour": end_hour}
                    )

        # Remove boxes with no available slots
        available_boxes = {
            box_id: slots for box_id, slots in availability.items() if slots
        }

        return {
            "next_available_hour": next_available_hour,
            "duration_hours": duration,
            "box_availability": available_boxes,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking availability: {str(e)}"
        )
