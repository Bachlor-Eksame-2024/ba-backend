from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from collections import defaultdict
from models import Boxes, Bookings, Users
from datetime import datetime, timedelta
from sqlalchemy import func

stats_router = APIRouter()

###################
#### GET STATS ####


@stats_router.get("/get-stats")
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
            {"name": date, "pv": count} for date, count in booking_dict.items()
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
