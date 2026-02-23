#!/usr/bin/env python3
"""
Export SQLite data to JSON for migration to PostgreSQL.
Run locally before deploying to Railway.

Usage:
    python scripts/export_data.py

Output:
    scripts/data_export.json
"""
import os
import sys
import json
from datetime import date, datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models import TrainingPlan, PlannedWorkout, ActualRun, RunSplit, RunWeather, RunNote


def serialize_value(value):
    """Convert value to JSON-serializable format."""
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return value
    return value


def export_model(db: Session, model_class, name: str) -> list:
    """Export all records from a model."""
    records = db.query(model_class).all()
    data = []

    for record in records:
        record_dict = {}
        for column in record.__table__.columns:
            value = getattr(record, column.name)
            record_dict[column.name] = serialize_value(value)
        data.append(record_dict)

    print(f"Exported {len(data)} {name} records")
    return data


def main():
    """Export all data to JSON."""
    print("=== Exporting SQLite Data ===\n")

    db = SessionLocal()

    try:
        export = {
            "exported_at": datetime.now().isoformat(),
            "training_plans": export_model(db, TrainingPlan, "training_plans"),
            "planned_workouts": export_model(db, PlannedWorkout, "planned_workouts"),
            "actual_runs": export_model(db, ActualRun, "actual_runs"),
            "run_splits": export_model(db, RunSplit, "run_splits"),
            "run_weather": export_model(db, RunWeather, "run_weather"),
            "run_notes": export_model(db, RunNote, "run_notes"),
        }

        # Write to file
        output_path = os.path.join(os.path.dirname(__file__), "data_export.json")
        with open(output_path, "w") as f:
            json.dump(export, f, indent=2)

        print(f"\nData exported to: {output_path}")
        print(f"File size: {os.path.getsize(output_path) / 1024:.1f} KB")

    finally:
        db.close()


if __name__ == "__main__":
    main()
