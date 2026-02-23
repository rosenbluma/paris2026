"""Training plan schemas."""
from pydantic import BaseModel
from datetime import date
from typing import Optional, List


class TrainingPlanBase(BaseModel):
    name: str
    start_date: date
    race_date: date
    target_time: Optional[str] = None
    target_pace: Optional[str] = None
    units: str = "miles"


class TrainingPlanCreate(TrainingPlanBase):
    pass


class TrainingPlanUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    race_date: Optional[date] = None
    target_time: Optional[str] = None
    target_pace: Optional[str] = None
    units: Optional[str] = None


class TrainingPlanResponse(TrainingPlanBase):
    id: int

    class Config:
        from_attributes = True


class TrainingPlanWithWorkouts(TrainingPlanResponse):
    workouts: List["WorkoutWithDetails"] = []

    class Config:
        from_attributes = True


# Forward reference resolution
from app.schemas.workout import WorkoutWithDetails
TrainingPlanWithWorkouts.model_rebuild()
