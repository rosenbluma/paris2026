"""Run notes and journal entries."""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class RunNote(Base):
    __tablename__ = "run_notes"

    id = Column(Integer, primary_key=True, index=True)
    planned_workout_id = Column(Integer, ForeignKey("planned_workouts.id"), unique=True)

    content = Column(Text)  # Markdown content
    mood_rating = Column(Integer)  # 1-5
    effort_rating = Column(Integer)  # 1-10 RPE
    audio = Column(String)  # music, audiobook, conversation, none
    tags = Column(JSON)  # ["tired", "great weather", etc.]

    # Fueling log
    fueling_log = Column(JSON)  # [{"type": "gel", "time": "30:00", "brand": "GU"}, ...]

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    planned_workout = relationship("PlannedWorkout", back_populates="note")
