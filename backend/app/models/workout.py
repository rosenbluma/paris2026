"""Planned workout model."""
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class PlannedWorkout(Base):
    __tablename__ = "planned_workouts"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("training_plans.id"), nullable=False)

    week = Column(Integer, nullable=False)  # 1-10
    day_of_week = Column(String, nullable=False)  # Mon, Tue, etc.
    date = Column(Date, nullable=False)

    workout_type = Column(String, nullable=False)  # Easy Run, Long Run, Rest, etc.
    target_distance = Column(Float)  # in miles
    target_pace = Column(String)  # e.g., "Easy conversational"
    description = Column(Text)
    fueling = Column(String)  # None, Water, Gel, etc.

    # Sleep data from Garmin (night before this workout)
    sleep_hours = Column(Float)  # Total sleep in hours
    hrv = Column(Integer)  # HRV (heart rate variability) in ms from previous night

    # Relationships
    plan = relationship("TrainingPlan", back_populates="workouts")
    actual_run = relationship("ActualRun", back_populates="planned_workout", uselist=False)
    note = relationship("RunNote", back_populates="planned_workout", uselist=False)
