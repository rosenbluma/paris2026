"""Garmin sync API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import os

from app.database import get_db
from app.services.garmin_sync import GarminSyncService, TOKEN_PATH

router = APIRouter(prefix="/api/sync", tags=["Sync"])

# Store Garmin session
garmin_service: Optional[GarminSyncService] = None


@router.post("/garmin/login")
async def garmin_login(email: str = Query(...), password: str = Query(...)):
    """Login to Garmin Connect."""
    global garmin_service
    try:
        garmin_service = GarminSyncService(email, password)
        await garmin_service.login()
        return {"status": "connected", "message": "Successfully connected to Garmin Connect"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Garmin login failed: {str(e)}")


@router.get("/garmin/status")
async def garmin_status():
    """Check Garmin connection status."""
    global garmin_service

    # Check if we have saved tokens
    if os.path.exists(TOKEN_PATH):
        return {"status": "connected", "message": "Using saved tokens"}

    if garmin_service is None:
        return {"status": "disconnected"}

    return {"status": "connected"}


@router.post("/garmin/activities")
async def sync_activities(
    plan_id: int = Query(...),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """Sync activities from Garmin Connect."""
    global garmin_service

    # Try to use saved tokens if no active session
    if garmin_service is None and os.path.exists(TOKEN_PATH):
        try:
            from garminconnect import Garmin
            garmin_service = GarminSyncService("", "")
            garmin_service.client = Garmin()
            garmin_service.client.garth.load(TOKEN_PATH)
            # Test connection
            garmin_service.client.display_name
            print("Using saved Garmin tokens")
        except Exception as e:
            print(f"Failed to load saved tokens: {e}")
            garmin_service = None

    if garmin_service is None or garmin_service.client is None:
        raise HTTPException(status_code=401, detail="Not connected to Garmin. Please login first or run: python garmin_login.py")

    try:
        synced = await garmin_service.sync_activities(
            db=db,
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
        )
        return {
            "status": "success",
            "activities_synced": len(synced),
            "activities": synced,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/garmin/logout")
async def garmin_logout():
    """Logout from Garmin Connect."""
    global garmin_service
    garmin_service = None

    # Remove saved tokens
    if os.path.exists(TOKEN_PATH):
        os.remove(TOKEN_PATH)

    return {"status": "disconnected"}
