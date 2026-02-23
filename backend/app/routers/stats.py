"""Stats and analysis API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date, timedelta

from app.database import get_db
from app.models import TrainingPlan, PlannedWorkout, ActualRun

router = APIRouter(prefix="/api/stats", tags=["Stats"])


@router.get("/summary")
def get_summary(plan_id: int = Query(...), db: Session = Depends(get_db)):
    """Get overall training summary stats."""
    plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not plan:
        return {"error": "Plan not found"}

    # Count workouts and completions
    total_workouts = db.query(PlannedWorkout).filter(PlannedWorkout.plan_id == plan_id).count()
    run_workouts = (
        db.query(PlannedWorkout)
        .filter(PlannedWorkout.plan_id == plan_id)
        .filter(PlannedWorkout.workout_type.notin_(["Rest", "Mobility"]))
        .count()
    )
    completed_runs = (
        db.query(PlannedWorkout)
        .join(ActualRun)
        .filter(PlannedWorkout.plan_id == plan_id)
        .count()
    )

    # Total miles planned vs completed
    total_planned = (
        db.query(func.sum(PlannedWorkout.target_distance))
        .filter(PlannedWorkout.plan_id == plan_id)
        .scalar() or 0
    )
    total_actual = (
        db.query(func.sum(ActualRun.distance))
        .join(PlannedWorkout)
        .filter(PlannedWorkout.plan_id == plan_id)
        .scalar() or 0
    )

    # Days until race
    days_until_race = (plan.race_date - date.today()).days

    # Current week
    if plan.start_date <= date.today():
        days_since_start = (date.today() - plan.start_date).days
        current_week = min((days_since_start // 7) + 1, 10)
    else:
        current_week = 0

    return {
        "plan_name": plan.name,
        "race_date": plan.race_date.isoformat(),
        "days_until_race": days_until_race,
        "current_week": current_week,
        "total_workouts": total_workouts,
        "run_workouts": run_workouts,
        "completed_runs": completed_runs,
        "completion_rate": round(completed_runs / run_workouts * 100, 1) if run_workouts > 0 else 0,
        "total_planned_miles": round(total_planned, 1),
        "total_actual_miles": round(total_actual, 1),
        "miles_remaining": round(total_planned - total_actual, 1),
    }


@router.get("/weekly")
def get_weekly_stats(plan_id: int = Query(...), db: Session = Depends(get_db)):
    """Get weekly mileage breakdown."""
    weeks = []
    for week_num in range(1, 11):
        # Planned miles
        planned = (
            db.query(func.sum(PlannedWorkout.target_distance))
            .filter(PlannedWorkout.plan_id == plan_id)
            .filter(PlannedWorkout.week == week_num)
            .scalar() or 0
        )

        # Actual miles
        actual = (
            db.query(func.sum(ActualRun.distance))
            .join(PlannedWorkout)
            .filter(PlannedWorkout.plan_id == plan_id)
            .filter(PlannedWorkout.week == week_num)
            .scalar() or 0
        )

        # Workouts completed
        completed = (
            db.query(PlannedWorkout)
            .join(ActualRun)
            .filter(PlannedWorkout.plan_id == plan_id)
            .filter(PlannedWorkout.week == week_num)
            .count()
        )

        total_runs = (
            db.query(PlannedWorkout)
            .filter(PlannedWorkout.plan_id == plan_id)
            .filter(PlannedWorkout.week == week_num)
            .filter(PlannedWorkout.workout_type.notin_(["Rest", "Mobility"]))
            .count()
        )

        weeks.append({
            "week": week_num,
            "planned_miles": round(planned, 1),
            "actual_miles": round(actual, 1),
            "total_runs": total_runs,
            "completed_runs": completed,
        })

    return weeks


@router.get("/pace-trend")
def get_pace_trend(plan_id: int = Query(...), db: Session = Depends(get_db)):
    """Get pace trend over time."""
    runs = (
        db.query(ActualRun)
        .join(PlannedWorkout)
        .filter(PlannedWorkout.plan_id == plan_id)
        .order_by(ActualRun.started_at)
        .all()
    )

    return [
        {
            "date": run.started_at.isoformat() if run.started_at else None,
            "pace": run.pace,
            "pace_seconds": run.pace_seconds,
            "distance": run.distance,
            "workout_type": run.planned_workout.workout_type if run.planned_workout else None,
        }
        for run in runs
    ]


@router.get("/hr-zones")
def get_hr_zone_distribution(plan_id: int = Query(...), db: Session = Depends(get_db)):
    """Get aggregate HR zone distribution."""
    runs = (
        db.query(ActualRun)
        .join(PlannedWorkout)
        .filter(PlannedWorkout.plan_id == plan_id)
        .filter(ActualRun.hr_zones.isnot(None))
        .all()
    )

    total_zones = {"zone1": 0, "zone2": 0, "zone3": 0, "zone4": 0, "zone5": 0}
    for run in runs:
        if run.hr_zones:
            for zone, seconds in run.hr_zones.items():
                if zone in total_zones:
                    total_zones[zone] += seconds

    return total_zones


@router.get("/countdown")
def get_countdown(plan_id: int = Query(...), db: Session = Depends(get_db)):
    """Get race countdown info."""
    plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not plan:
        return {"error": "Plan not found"}

    today = date.today()
    days_left = (plan.race_date - today).days
    weeks_left = days_left // 7
    days_remainder = days_left % 7

    return {
        "race_date": plan.race_date.isoformat(),
        "race_name": plan.name,
        "days_left": days_left,
        "weeks_left": weeks_left,
        "days_remainder": days_remainder,
        "target_pace": plan.target_pace,
        "target_time": plan.target_time,
    }
