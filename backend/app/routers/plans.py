"""Training plan API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database import get_db
from app.models import TrainingPlan, PlannedWorkout
from app.schemas import (
    TrainingPlanCreate,
    TrainingPlanUpdate,
    TrainingPlanResponse,
    TrainingPlanWithWorkouts,
)

router = APIRouter(prefix="/api/plans", tags=["Training Plans"])


@router.get("/", response_model=List[TrainingPlanResponse])
def list_plans(db: Session = Depends(get_db)):
    """List all training plans."""
    return db.query(TrainingPlan).all()


@router.post("/", response_model=TrainingPlanResponse)
def create_plan(plan: TrainingPlanCreate, db: Session = Depends(get_db)):
    """Create a new training plan."""
    db_plan = TrainingPlan(**plan.model_dump())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan


@router.get("/{plan_id}", response_model=TrainingPlanWithWorkouts)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """Get a training plan with all workouts."""
    plan = (
        db.query(TrainingPlan)
        .options(
            joinedload(TrainingPlan.workouts)
            .joinedload(PlannedWorkout.actual_run),
            joinedload(TrainingPlan.workouts)
            .joinedload(PlannedWorkout.note),
        )
        .filter(TrainingPlan.id == plan_id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found")
    return plan


@router.patch("/{plan_id}", response_model=TrainingPlanResponse)
def update_plan(plan_id: int, plan_update: TrainingPlanUpdate, db: Session = Depends(get_db)):
    """Update a training plan."""
    plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found")

    update_data = plan_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/{plan_id}")
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    """Delete a training plan."""
    plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found")

    db.delete(plan)
    db.commit()
    return {"message": "Training plan deleted"}
