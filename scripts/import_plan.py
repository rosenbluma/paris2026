#!/usr/bin/env python3
"""Import training plan from JSON into the database."""
import json
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal, init_db
from app.models import TrainingPlan, PlannedWorkout, ActualRun, RunNote


def parse_pace_to_seconds(pace_str: str) -> int:
    """Convert pace string like '10:02/mi' to seconds."""
    if not pace_str:
        return 0
    # Remove '/mi' suffix
    pace = pace_str.replace("/mi", "").replace("/mile", "").strip()
    parts = pace.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return 0


def import_plan(json_path: str):
    """Import training plan from JSON file."""
    # Initialize database
    init_db()

    with open(json_path, "r") as f:
        data = json.load(f)

    db = SessionLocal()

    try:
        # Check if plan already exists
        existing = db.query(TrainingPlan).filter(TrainingPlan.name == data["name"]).first()
        if existing:
            print(f"Plan '{data['name']}' already exists. Deleting and reimporting...")
            db.delete(existing)
            db.commit()

        # Create training plan
        plan = TrainingPlan(
            name=data["name"],
            start_date=datetime.strptime(data["start_date"], "%Y-%m-%d").date(),
            race_date=datetime.strptime(data["race_date"], "%Y-%m-%d").date(),
            target_time=data.get("target_time"),
            target_pace=data.get("target_pace"),
            units=data.get("units", "miles"),
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        print(f"Created plan: {plan.name} (ID: {plan.id})")
        print(f"Race date: {plan.race_date}")
        print(f"Target: {plan.target_time} ({plan.target_pace})")
        print()

        # Import workouts
        workout_count = 0
        run_count = 0
        note_count = 0

        for workout_data in data["workouts"]:
            workout = PlannedWorkout(
                plan_id=plan.id,
                week=workout_data["week"],
                day_of_week=workout_data["day"],
                date=datetime.strptime(workout_data["date"], "%Y-%m-%d").date(),
                workout_type=workout_data["type"],
                target_distance=workout_data.get("distance"),
                target_pace=workout_data.get("pace_guidance"),
                fueling=workout_data.get("fueling"),
            )
            db.add(workout)
            db.commit()
            db.refresh(workout)
            workout_count += 1

            # Import actual run if exists
            if "actual" in workout_data:
                actual = workout_data["actual"]
                pace_seconds = parse_pace_to_seconds(actual.get("pace", ""))
                duration = int(actual.get("distance", 0) * pace_seconds)

                run = ActualRun(
                    planned_workout_id=workout.id,
                    distance=actual.get("distance"),
                    duration_seconds=duration,
                    pace=actual.get("pace"),
                    pace_seconds=pace_seconds,
                    avg_hr=actual.get("avg_hr"),
                    started_at=datetime.strptime(workout_data["date"], "%Y-%m-%d"),
                )
                db.add(run)
                db.commit()
                run_count += 1

                # Import note if exists
                if "notes" in actual:
                    note = RunNote(
                        planned_workout_id=workout.id,
                        content=actual["notes"],
                    )
                    db.add(note)
                    db.commit()
                    note_count += 1

        print(f"Imported {workout_count} workouts")
        print(f"Imported {run_count} actual runs")
        print(f"Imported {note_count} notes")
        print()
        print("Import complete!")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    json_path = os.path.join(os.path.dirname(__file__), "..", "data", "training_plan.json")
    import_plan(json_path)
