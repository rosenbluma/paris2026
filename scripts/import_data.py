#!/usr/bin/env python3
"""
Import JSON data into PostgreSQL on Railway.
Run after deploying to Railway with DATABASE_URL set.

Usage:
    DATABASE_URL=postgresql://... python scripts/import_data.py

Or run on Railway:
    railway run python scripts/import_data.py
"""
import os
import sys
import json
from datetime import date, datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import engine, SessionLocal, SQLALCHEMY_DATABASE_URL
from app.models import TrainingPlan, PlannedWorkout, ActualRun, RunSplit, RunWeather, RunNote


def parse_date(value):
    """Parse date from ISO format string."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except:
        return datetime.fromisoformat(value).date()


def parse_datetime(value):
    """Parse datetime from ISO format string."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except:
        return None


def import_training_plans(db: Session, data: list):
    """Import training plans."""
    for record in data:
        plan = TrainingPlan(
            id=record["id"],
            race_name=record["race_name"],
            race_date=parse_date(record["race_date"]),
            start_date=parse_date(record["start_date"]),
            target_time=record.get("target_time"),
            target_pace=record.get("target_pace"),
        )
        db.merge(plan)
    db.commit()
    print(f"Imported {len(data)} training plans")


def import_planned_workouts(db: Session, data: list):
    """Import planned workouts."""
    for record in data:
        workout = PlannedWorkout(
            id=record["id"],
            plan_id=record["plan_id"],
            week=record["week"],
            day_of_week=record["day_of_week"],
            date=parse_date(record["date"]),
            workout_type=record["workout_type"],
            target_distance=record.get("target_distance"),
            target_pace=record.get("target_pace"),
            description=record.get("description"),
            fueling=record.get("fueling"),
            sleep_hours=record.get("sleep_hours"),
            hrv=record.get("hrv"),
        )
        db.merge(workout)
    db.commit()
    print(f"Imported {len(data)} planned workouts")


def import_actual_runs(db: Session, data: list):
    """Import actual runs."""
    for record in data:
        run = ActualRun(
            id=record["id"],
            planned_workout_id=record.get("planned_workout_id"),
            garmin_activity_id=record.get("garmin_activity_id"),
            distance=record["distance"],
            duration_seconds=record["duration_seconds"],
            pace=record["pace"],
            pace_seconds=record["pace_seconds"],
            avg_hr=record.get("avg_hr"),
            max_hr=record.get("max_hr"),
            hr_zones=record.get("hr_zones"),
            elevation_gain=record.get("elevation_gain"),
            cadence=record.get("cadence"),
            calories=record.get("calories"),
            training_effect_aerobic=record.get("training_effect_aerobic"),
            training_effect_anaerobic=record.get("training_effect_anaerobic"),
            vo2max=record.get("vo2max"),
            start_lat=record.get("start_lat"),
            start_lon=record.get("start_lon"),
            started_at=parse_datetime(record.get("started_at")),
            raw_data=record.get("raw_data"),
        )
        db.merge(run)
    db.commit()
    print(f"Imported {len(data)} actual runs")


def import_run_splits(db: Session, data: list):
    """Import run splits."""
    for record in data:
        split = RunSplit(
            id=record["id"],
            run_id=record["run_id"],
            split_number=record["split_number"],
            distance=record["distance"],
            duration_seconds=record["duration_seconds"],
            pace=record["pace"],
            pace_seconds=record["pace_seconds"],
            avg_hr=record.get("avg_hr"),
            elevation_gain=record.get("elevation_gain"),
            cadence=record.get("cadence"),
        )
        db.merge(split)
    db.commit()
    print(f"Imported {len(data)} run splits")


def import_run_weather(db: Session, data: list):
    """Import run weather."""
    for record in data:
        weather = RunWeather(
            id=record["id"],
            run_id=record["run_id"],
            temperature=record.get("temperature"),
            feels_like=record.get("feels_like"),
            humidity=record.get("humidity"),
            wind_speed=record.get("wind_speed"),
            wind_direction=record.get("wind_direction"),
            conditions=record.get("conditions"),
            precipitation=record.get("precipitation"),
        )
        db.merge(weather)
    db.commit()
    print(f"Imported {len(data)} run weather records")


def import_run_notes(db: Session, data: list):
    """Import run notes."""
    for record in data:
        note = RunNote(
            id=record["id"],
            planned_workout_id=record["planned_workout_id"],
            content=record.get("content"),
            mood_rating=record.get("mood_rating"),
            effort_rating=record.get("effort_rating"),
            audio=record.get("audio"),
            tags=record.get("tags"),
            fueling_log=record.get("fueling_log"),
            created_at=parse_datetime(record.get("created_at")) or datetime.now(),
            updated_at=parse_datetime(record.get("updated_at")) or datetime.now(),
        )
        db.merge(note)
    db.commit()
    print(f"Imported {len(data)} run notes")


def reset_sequences(db: Session):
    """Reset PostgreSQL sequences to max ID + 1."""
    if "postgresql" not in SQLALCHEMY_DATABASE_URL:
        return

    tables = [
        ("training_plans", "id"),
        ("planned_workouts", "id"),
        ("actual_runs", "id"),
        ("run_splits", "id"),
        ("run_weather", "id"),
        ("run_notes", "id"),
    ]

    for table, column in tables:
        try:
            db.execute(text(f"""
                SELECT setval(pg_get_serial_sequence('{table}', '{column}'),
                       COALESCE((SELECT MAX({column}) FROM {table}), 0) + 1, false)
            """))
        except Exception as e:
            print(f"Warning: Could not reset sequence for {table}: {e}")

    db.commit()
    print("Reset PostgreSQL sequences")


def main():
    """Import data from JSON."""
    print("=== Importing Data to PostgreSQL ===\n")
    print(f"Database: {SQLALCHEMY_DATABASE_URL[:50]}...")

    # Check for DATABASE_URL
    if "sqlite" in SQLALCHEMY_DATABASE_URL:
        print("\nWARNING: DATABASE_URL not set, using SQLite!")
        print("Set DATABASE_URL to your Railway PostgreSQL connection string.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != "y":
            sys.exit(1)

    # Load export file
    export_path = os.path.join(os.path.dirname(__file__), "data_export.json")
    if not os.path.exists(export_path):
        print(f"ERROR: Export file not found: {export_path}")
        print("Run 'python scripts/export_data.py' first")
        sys.exit(1)

    with open(export_path, "r") as f:
        data = json.load(f)

    print(f"Loaded export from: {data.get('exported_at', 'unknown')}\n")

    db = SessionLocal()

    try:
        # Import in order (respecting foreign keys)
        import_training_plans(db, data.get("training_plans", []))
        import_planned_workouts(db, data.get("planned_workouts", []))
        import_actual_runs(db, data.get("actual_runs", []))
        import_run_splits(db, data.get("run_splits", []))
        import_run_weather(db, data.get("run_weather", []))
        import_run_notes(db, data.get("run_notes", []))

        # Reset sequences for PostgreSQL
        reset_sequences(db)

        print("\nImport completed successfully!")

    except Exception as e:
        print(f"\nERROR during import: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
