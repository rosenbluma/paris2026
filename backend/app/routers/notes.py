"""Run notes API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import RunNote, PlannedWorkout
from app.schemas import RunNoteCreate, RunNoteUpdate, RunNoteResponse

router = APIRouter(prefix="/api/notes", tags=["Notes"])


@router.get("/", response_model=List[RunNoteResponse])
def list_notes(db: Session = Depends(get_db)):
    """List all notes."""
    return db.query(RunNote).order_by(RunNote.created_at.desc()).all()


@router.post("/", response_model=RunNoteResponse)
def create_note(note: RunNoteCreate, db: Session = Depends(get_db)):
    """Create a note for a workout."""
    # Check workout exists
    workout = db.query(PlannedWorkout).filter(PlannedWorkout.id == note.planned_workout_id).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    # Check if note already exists
    existing = db.query(RunNote).filter(RunNote.planned_workout_id == note.planned_workout_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Note already exists for this workout")

    db_note = RunNote(**note.model_dump())
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


@router.get("/{note_id}", response_model=RunNoteResponse)
def get_note(note_id: int, db: Session = Depends(get_db)):
    """Get a note."""
    note = db.query(RunNote).filter(RunNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.get("/workout/{workout_id}", response_model=RunNoteResponse)
def get_note_by_workout(workout_id: int, db: Session = Depends(get_db)):
    """Get note for a specific workout."""
    note = db.query(RunNote).filter(RunNote.planned_workout_id == workout_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found for this workout")
    return note


@router.patch("/{note_id}", response_model=RunNoteResponse)
def update_note(note_id: int, note_update: RunNoteUpdate, db: Session = Depends(get_db)):
    """Update a note."""
    note = db.query(RunNote).filter(RunNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    update_data = note_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)

    db.commit()
    db.refresh(note)
    return note


@router.put("/workout/{workout_id}", response_model=RunNoteResponse)
def upsert_note_by_workout(workout_id: int, note_data: RunNoteUpdate, db: Session = Depends(get_db)):
    """Create or update a note for a workout."""
    # Check workout exists
    workout = db.query(PlannedWorkout).filter(PlannedWorkout.id == workout_id).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    # Try to find existing note
    note = db.query(RunNote).filter(RunNote.planned_workout_id == workout_id).first()

    if note:
        # Update existing
        update_data = note_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(note, field, value)
    else:
        # Create new
        note = RunNote(
            planned_workout_id=workout_id,
            **note_data.model_dump(exclude_unset=True)
        )
        db.add(note)

    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a note."""
    note = db.query(RunNote).filter(RunNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    db.delete(note)
    db.commit()
    return {"message": "Note deleted"}
