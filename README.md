# Paris 2026 Marathon Training Tracker

A web app to track your marathon training journey to the Paris Marathon on April 11, 2026.

## Quick Start

### 1. Start the Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Import the training plan
cd ..
python scripts/import_plan.py

# Start the server
cd backend
uvicorn app.main:app --reload --port 8000
```

### 2. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## Features

- **Training Plan View** - 10-week training schedule with expandable week details
- **Workout Editing** - Update workout types and details
- **Garmin Sync** - Connect to Garmin Connect to sync your runs
- **Notes & Journaling** - Add notes, mood, and effort ratings to each workout
- **Progress Tracking** - Race countdown and completion stats

## Tech Stack

- **Backend**: FastAPI + SQLite + python-garminconnect
- **Frontend**: React + Vite + TailwindCSS
- **Database**: SQLite (data/marathon.db)

## Project Structure

```
paris2026/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI entry point
│   │   ├── database.py       # SQLite setup
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── routers/          # API routes
│   │   └── services/         # Garmin & Weather services
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/            # Plan page
│   │   ├── components/       # React components
│   │   └── api/              # API client
│   └── package.json
├── data/
│   ├── marathon.db           # SQLite database
│   └── training_plan.json    # Training plan data
└── scripts/
    └── import_plan.py        # Import script
```

## Training Plan

- **Duration**: 10 weeks (Feb 1 - Apr 11, 2026)
- **Total Miles**: ~235 miles
- **Target Pace**: 9:09/mile
- **Target Time**: 4:00:00

Good luck with your training!
