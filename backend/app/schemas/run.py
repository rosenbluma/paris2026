"""Actual run schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class RunSplitBase(BaseModel):
    split_number: int
    distance: float
    duration_seconds: int
    pace: str
    pace_seconds: int
    avg_hr: Optional[int] = None
    elevation_gain: Optional[float] = None
    cadence: Optional[int] = None


class RunSplitCreate(RunSplitBase):
    run_id: int


class RunSplitResponse(RunSplitBase):
    id: int

    class Config:
        from_attributes = True


class RunWeatherBase(BaseModel):
    temperature: Optional[float] = None
    feels_like: Optional[float] = None
    humidity: Optional[int] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[str] = None
    conditions: Optional[str] = None
    precipitation: Optional[float] = None


class RunWeatherCreate(RunWeatherBase):
    run_id: int


class RunWeatherResponse(RunWeatherBase):
    id: int

    class Config:
        from_attributes = True


class ActualRunBase(BaseModel):
    distance: float
    duration_seconds: int
    pace: str
    pace_seconds: int
    avg_hr: Optional[int] = None
    max_hr: Optional[int] = None
    hr_zones: Optional[Dict[str, int]] = None
    elevation_gain: Optional[float] = None
    cadence: Optional[float] = None
    calories: Optional[int] = None
    training_effect_aerobic: Optional[float] = None
    training_effect_anaerobic: Optional[float] = None
    vo2max: Optional[float] = None
    start_lat: Optional[float] = None
    start_lon: Optional[float] = None
    started_at: Optional[datetime] = None


class ActualRunCreate(ActualRunBase):
    planned_workout_id: Optional[int] = None
    garmin_activity_id: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class ActualRunResponse(ActualRunBase):
    id: int
    planned_workout_id: Optional[int] = None
    garmin_activity_id: Optional[str] = None

    class Config:
        from_attributes = True


class RunWithDetails(ActualRunResponse):
    splits: List[RunSplitResponse] = []
    weather: Optional[RunWeatherResponse] = None

    class Config:
        from_attributes = True
