#!/usr/bin/env python3
"""
Standalone cron script for daily Garmin sync.
Run on Railway as a cron service with schedule: 0 6 * * *

Environment variables required:
- DATABASE_URL: PostgreSQL connection string
- GARMIN_TOKEN_DATA: Base64-encoded Garmin tokens (from .garmin_tokens directory)
"""
import os
import sys
import json
import base64
import asyncio
import tempfile
from datetime import date, timedelta

# Add the app to the path
sys.path.insert(0, os.path.dirname(__file__))

from garminconnect import Garmin
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models import TrainingPlan, PlannedWorkout, ActualRun
from app.services.garmin_sync import GarminSyncService


def load_garmin_tokens():
    """Load Garmin tokens from GARMIN_TOKEN_DATA env var."""
    token_data = os.environ.get("GARMIN_TOKEN_DATA")
    if not token_data:
        print("ERROR: GARMIN_TOKEN_DATA environment variable not set")
        print("Export your local .garmin_tokens using: python scripts/export_garmin_tokens.py")
        sys.exit(1)

    # Decode base64 token data
    try:
        tokens = json.loads(base64.b64decode(token_data).decode("utf-8"))
    except Exception as e:
        print(f"ERROR: Failed to decode GARMIN_TOKEN_DATA: {e}")
        sys.exit(1)

    # Write tokens to temp directory for garth to load
    temp_dir = tempfile.mkdtemp()
    for filename, content in tokens.items():
        filepath = os.path.join(temp_dir, filename)
        with open(filepath, "w") as f:
            json.dump(content, f)

    return temp_dir


async def sync_active_plans(db: Session, token_path: str):
    """Sync Garmin data for all active training plans."""
    today = date.today()

    # Find active training plans (current date is between start and race date)
    active_plans = (
        db.query(TrainingPlan)
        .filter(TrainingPlan.start_date <= today)
        .filter(TrainingPlan.race_date >= today)
        .all()
    )

    if not active_plans:
        print("No active training plans found")
        return

    print(f"Found {len(active_plans)} active training plan(s)")

    # Initialize Garmin client with saved tokens
    client = Garmin()
    try:
        client.garth.load(token_path)
        # Test connection
        display_name = client.display_name
        print(f"Connected to Garmin as: {display_name}")
    except Exception as e:
        print(f"ERROR: Failed to load Garmin tokens: {e}")
        sys.exit(1)

    # Create sync service with loaded client
    sync_service = GarminSyncService("", "")
    sync_service.client = client

    # Sync last 7 days for each active plan
    start_date = today - timedelta(days=7)
    end_date = today

    for plan in active_plans:
        print(f"\nSyncing plan: {plan.race_name} (ID: {plan.id})")
        try:
            synced = await sync_service.sync_activities(
                db=db,
                plan_id=plan.id,
                start_date=start_date,
                end_date=end_date,
            )
            print(f"Synced {len(synced)} activities for plan {plan.id}")
        except Exception as e:
            print(f"ERROR syncing plan {plan.id}: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Main entry point for cron sync."""
    print("=" * 50)
    print("Garmin Sync Cron Job Started")
    print(f"Date: {date.today()}")
    print("=" * 50)

    # Load tokens
    token_path = load_garmin_tokens()
    print(f"Tokens loaded to: {token_path}")

    # Create database session
    db = SessionLocal()

    try:
        await sync_active_plans(db, token_path)
        print("\nSync completed successfully!")
    except Exception as e:
        print(f"\nERROR during sync: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()
        # Cleanup temp token directory
        import shutil
        shutil.rmtree(token_path, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
