"""Planned workout API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.models import PlannedWorkout, ActualRun
from app.schemas import (
    PlannedWorkoutCreate,
    PlannedWorkoutUpdate,
    PlannedWorkoutResponse,
    WorkoutWithDetails,
)

router = APIRouter(prefix="/api/workouts", tags=["Workouts"])


@router.get("/", response_model=List[WorkoutWithDetails])
def list_workouts(
    plan_id: Optional[int] = Query(None),
    week: Optional[int] = Query(None),
    workout_type: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """List workouts with optional filters."""
    query = (
        db.query(PlannedWorkout)
        .options(
            joinedload(PlannedWorkout.actual_run).joinedload(ActualRun.weather),
            joinedload(PlannedWorkout.note),
        )
    )

    if plan_id:
        query = query.filter(PlannedWorkout.plan_id == plan_id)
    if week:
        query = query.filter(PlannedWorkout.week == week)
    if workout_type:
        query = query.filter(PlannedWorkout.workout_type == workout_type)
    if start_date:
        query = query.filter(PlannedWorkout.date >= start_date)
    if end_date:
        query = query.filter(PlannedWorkout.date <= end_date)

    return query.order_by(PlannedWorkout.date).all()


@router.post("/", response_model=PlannedWorkoutResponse)
def create_workout(workout: PlannedWorkoutCreate, db: Session = Depends(get_db)):
    """Create a new planned workout."""
    db_workout = PlannedWorkout(**workout.model_dump())
    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    return db_workout


@router.get("/{workout_id}", response_model=WorkoutWithDetails)
def get_workout(workout_id: int, db: Session = Depends(get_db)):
    """Get a workout with actual run and notes."""
    workout = (
        db.query(PlannedWorkout)
        .options(
            joinedload(PlannedWorkout.actual_run).joinedload(ActualRun.splits),
            joinedload(PlannedWorkout.actual_run).joinedload(ActualRun.weather),
            joinedload(PlannedWorkout.note),
        )
        .filter(PlannedWorkout.id == workout_id)
        .first()
    )
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout


@router.patch("/{workout_id}", response_model=PlannedWorkoutResponse)
def update_workout(workout_id: int, workout_update: PlannedWorkoutUpdate, db: Session = Depends(get_db)):
    """Update a planned workout."""
    workout = db.query(PlannedWorkout).filter(PlannedWorkout.id == workout_id).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    update_data = workout_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workout, field, value)

    db.commit()
    db.refresh(workout)
    return workout


@router.delete("/{workout_id}")
def delete_workout(workout_id: int, db: Session = Depends(get_db)):
    """Delete a planned workout."""
    workout = db.query(PlannedWorkout).filter(PlannedWorkout.id == workout_id).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    db.delete(workout)
    db.commit()
    return {"message": "Workout deleted"}


@router.get("/today/", response_model=Optional[WorkoutWithDetails])
def get_todays_workout(plan_id: int = Query(...), db: Session = Depends(get_db)):
    """Get today's planned workout."""
    today = date.today()
    workout = (
        db.query(PlannedWorkout)
        .options(
            joinedload(PlannedWorkout.actual_run),
            joinedload(PlannedWorkout.note),
        )
        .filter(PlannedWorkout.plan_id == plan_id)
        .filter(PlannedWorkout.date == today)
        .first()
    )
    return workout


@router.get("/week/{week_num}", response_model=List[WorkoutWithDetails])
def get_week_workouts(week_num: int, plan_id: int = Query(...), db: Session = Depends(get_db)):
    """Get all workouts for a specific week."""
    workouts = (
        db.query(PlannedWorkout)
        .options(
            joinedload(PlannedWorkout.actual_run),
            joinedload(PlannedWorkout.note),
        )
        .filter(PlannedWorkout.plan_id == plan_id)
        .filter(PlannedWorkout.week == week_num)
        .order_by(PlannedWorkout.date)
        .all()
    )
    return workouts
