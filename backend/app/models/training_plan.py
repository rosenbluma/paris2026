"""Training plan model."""
from sqlalchemy import Column, Integer, String, Date, Time
from sqlalchemy.orm import relationship
from app.database import Base


class TrainingPlan(Base):
    __tablename__ = "training_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    race_date = Column(Date, nullable=False)
    target_time = Column(String)  # e.g., "4:00:00"
    target_pace = Column(String)  # e.g., "9:09/mile"
    units = Column(String, default="miles")

    # Relationships
    workouts = relationship("PlannedWorkout", back_populates="plan", cascade="all, delete-orphan")
