"""Actual run API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.models import ActualRun, RunSplit, RunWeather
from app.schemas import (
    ActualRunCreate,
    ActualRunResponse,
    RunWithDetails,
    RunSplitCreate,
    RunSplitResponse,
    RunWeatherCreate,
    RunWeatherResponse,
)

router = APIRouter(prefix="/api/runs", tags=["Runs"])


@router.get("/", response_model=List[RunWithDetails])
def list_runs(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List recent runs."""
    runs = (
        db.query(ActualRun)
        .options(
            joinedload(ActualRun.splits),
            joinedload(ActualRun.weather),
        )
        .order_by(ActualRun.started_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return runs


@router.post("/", response_model=ActualRunResponse)
def create_run(run: ActualRunCreate, db: Session = Depends(get_db)):
    """Create a new run record."""
    db_run = ActualRun(**run.model_dump())
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run


@router.get("/{run_id}", response_model=RunWithDetails)
def get_run(run_id: int, db: Session = Depends(get_db)):
    """Get a run with splits and weather."""
    run = (
        db.query(ActualRun)
        .options(
            joinedload(ActualRun.splits),
            joinedload(ActualRun.weather),
        )
        .filter(ActualRun.id == run_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.delete("/{run_id}")
def delete_run(run_id: int, db: Session = Depends(get_db)):
    """Delete a run."""
    run = db.query(ActualRun).filter(ActualRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    db.delete(run)
    db.commit()
    return {"message": "Run deleted"}


@router.post("/{run_id}/splits", response_model=RunSplitResponse)
def add_split(run_id: int, split: RunSplitCreate, db: Session = Depends(get_db)):
    """Add a split to a run."""
    run = db.query(ActualRun).filter(ActualRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    db_split = RunSplit(**split.model_dump())
    db_split.run_id = run_id
    db.add(db_split)
    db.commit()
    db.refresh(db_split)
    return db_split


@router.post("/{run_id}/weather", response_model=RunWeatherResponse)
def add_weather(run_id: int, weather: RunWeatherCreate, db: Session = Depends(get_db)):
    """Add weather data to a run."""
    run = db.query(ActualRun).filter(ActualRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Check if weather already exists
    existing = db.query(RunWeather).filter(RunWeather.run_id == run_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Weather already exists for this run")

    db_weather = RunWeather(**weather.model_dump())
    db_weather.run_id = run_id
    db.add(db_weather)
    db.commit()
    db.refresh(db_weather)
    return db_weather


@router.patch("/{run_id}/link/{workout_id}", response_model=ActualRunResponse)
def link_run_to_workout(run_id: int, workout_id: int, db: Session = Depends(get_db)):
    """Link a run to a planned workout."""
    run = db.query(ActualRun).filter(ActualRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    run.planned_workout_id = workout_id
    db.commit()
    db.refresh(run)
    return run
