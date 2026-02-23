"""Run note schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class FuelingEntry(BaseModel):
    type: str  # gel, water, electrolyte, etc.
    time: Optional[str] = None  # "30:00" into the run
    brand: Optional[str] = None
    notes: Optional[str] = None


class RunNoteBase(BaseModel):
    content: Optional[str] = None
    mood_rating: Optional[int] = None  # 1-5
    effort_rating: Optional[int] = None  # 1-10 RPE
    audio: Optional[str] = None  # music, audiobook, conversation, none
    tags: Optional[List[str]] = None
    fueling_log: Optional[List[Dict[str, Any]]] = None


class RunNoteCreate(RunNoteBase):
    planned_workout_id: int


class RunNoteUpdate(RunNoteBase):
    pass


class RunNoteResponse(RunNoteBase):
    id: int
    planned_workout_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
