"""Planned workout schemas."""
from pydantic import BaseModel
from datetime import date
from typing import Optional


class PlannedWorkoutBase(BaseModel):
    week: int
    day_of_week: str
    date: date
    workout_type: str
    target_distance: Optional[float] = None
    target_pace: Optional[str] = None
    description: Optional[str] = None
    fueling: Optional[str] = None
    sleep_hours: Optional[float] = None
    hrv: Optional[int] = None


class PlannedWorkoutCreate(PlannedWorkoutBase):
    plan_id: int


class PlannedWorkoutUpdate(BaseModel):
    week: Optional[int] = None
    day_of_week: Optional[str] = None
    date: Optional[date] = None
    workout_type: Optional[str] = None
    target_distance: Optional[float] = None
    target_pace: Optional[str] = None
    description: Optional[str] = None
    fueling: Optional[str] = None


class PlannedWorkoutResponse(PlannedWorkoutBase):
    id: int
    plan_id: int

    class Config:
        from_attributes = True


class WorkoutWithDetails(PlannedWorkoutResponse):
    actual_run: Optional["RunWithDetails"] = None
    note: Optional["RunNoteResponse"] = None

    class Config:
        from_attributes = True


# Forward reference resolution
from app.schemas.run import RunWithDetails
from app.schemas.note import RunNoteResponse
WorkoutWithDetails.model_rebuild()
