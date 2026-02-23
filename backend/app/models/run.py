"""Actual run and related models."""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class ActualRun(Base):
    __tablename__ = "actual_runs"

    id = Column(Integer, primary_key=True, index=True)
    planned_workout_id = Column(Integer, ForeignKey("planned_workouts.id"), unique=True)
    garmin_activity_id = Column(String, unique=True)  # Garmin's activity ID

    # Core metrics
    distance = Column(Float)  # miles
    duration_seconds = Column(Integer)
    pace = Column(String)  # e.g., "10:02/mi"
    pace_seconds = Column(Integer)  # seconds per mile for calculations

    # Heart rate
    avg_hr = Column(Integer)
    max_hr = Column(Integer)
    hr_zones = Column(JSON)  # {"zone1": 120, "zone2": 300, ...} seconds in each zone

    # Additional metrics
    elevation_gain = Column(Float)  # feet
    cadence = Column(Integer)  # steps per minute
    calories = Column(Integer)
    training_effect_aerobic = Column(Float)
    training_effect_anaerobic = Column(Float)
    vo2max = Column(Float)

    # GPS data
    start_lat = Column(Float)
    start_lon = Column(Float)

    # Timestamps
    started_at = Column(DateTime)

    # Raw Garmin data for future use
    raw_data = Column(JSON)

    # Relationships
    planned_workout = relationship("PlannedWorkout", back_populates="actual_run")
    splits = relationship("RunSplit", back_populates="run", cascade="all, delete-orphan")
    weather = relationship("RunWeather", back_populates="run", uselist=False, cascade="all, delete-orphan")


class RunSplit(Base):
    __tablename__ = "run_splits"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("actual_runs.id"), nullable=False)

    split_number = Column(Integer, nullable=False)  # 1, 2, 3...
    distance = Column(Float)  # miles (usually 1.0)
    duration_seconds = Column(Integer)
    pace = Column(String)  # e.g., "9:45/mi"
    pace_seconds = Column(Integer)
    avg_hr = Column(Integer)
    elevation_gain = Column(Float)
    cadence = Column(Integer)

    # Relationships
    run = relationship("ActualRun", back_populates="splits")


class RunWeather(Base):
    __tablename__ = "run_weather"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("actual_runs.id"), unique=True, nullable=False)

    temperature = Column(Float)  # Fahrenheit
    feels_like = Column(Float)
    humidity = Column(Integer)  # percentage
    wind_speed = Column(Float)  # mph
    wind_direction = Column(String)
    conditions = Column(String)  # Clear, Cloudy, Rain, etc.
    precipitation = Column(Float)  # inches

    # Relationships
    run = relationship("ActualRun", back_populates="weather")
