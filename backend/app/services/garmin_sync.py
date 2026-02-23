"""Garmin Connect sync service."""
from garminconnect import Garmin
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
import os

from app.models import PlannedWorkout, ActualRun, TrainingPlan, RunWeather
from app.services.weather import WeatherService

# Token storage path
TOKEN_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".garmin_tokens")


class GarminSyncService:
    """Service for syncing data from Garmin Connect."""

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.client: Optional[Garmin] = None
        self.weather_service = WeatherService()

    async def login(self):
        """Authenticate with Garmin Connect."""
        self.client = Garmin(self.email, self.password)

        # Try to load saved tokens first
        if os.path.exists(TOKEN_PATH):
            try:
                self.client.garth.load(TOKEN_PATH)
                # Test if tokens are still valid
                self.client.display_name
                print("Loaded saved Garmin session")
                return
            except Exception as e:
                print(f"Saved tokens expired, re-authenticating: {e}")

        # Fresh login
        self.client.login()

        # Save tokens for future use
        self.client.garth.dump(TOKEN_PATH)
        print("Garmin login successful, tokens saved")

    async def sync_activities(
        self,
        db: Session,
        plan_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Sync all running activities from Garmin for the training plan period."""
        if not self.client:
            raise ValueError("Not logged in to Garmin")

        # Get the training plan dates
        plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
        if plan:
            start_date = start_date or plan.start_date
            end_date = end_date or date.today()
        else:
            start_date = start_date or (date.today() - timedelta(days=60))
            end_date = end_date or date.today()

        print(f"Syncing Garmin activities from {start_date} to {end_date}")

        # Fetch all activities and filter locally for running types
        all_activities = self.client.get_activities_by_date(
            start_date.isoformat(),
            end_date.isoformat(),
        )

        # Filter for any activity with "running" in the type (outdoor, treadmill, indoor, track, etc.)
        activities = [
            a for a in all_activities
            if "running" in a.get("activityType", {}).get("typeKey", "").lower()
        ]

        print(f"Found {len(activities)} running activities (out of {len(all_activities)} total)")

        synced = []
        for activity in activities:
            activity_id = str(activity.get("activityId"))

            # Skip if already synced
            existing = db.query(ActualRun).filter(ActualRun.garmin_activity_id == activity_id).first()
            if existing:
                # If existing run has no weather, try to fetch it
                if not existing.weather and existing.start_lat and existing.started_at:
                    await self._fetch_weather_for_run(db, existing)
                print(f"Activity {activity_id} already synced, skipping")
                continue

            # Parse the activity date
            activity_date = self._parse_date(activity.get("startTimeLocal"))

            # Parse activity data
            distance = (activity.get("distance") or 0) / 1609.344  # meters to miles
            duration = int(activity.get("duration") or 0)  # seconds

            # Calculate pace
            if distance > 0:
                pace_sec = int(duration / distance)
                pace = f"{pace_sec // 60}:{pace_sec % 60:02d}/mi"
            else:
                pace_sec = 0
                pace = "0:00/mi"

            # Find matching planned workout by date
            planned = None
            if activity_date:
                planned = (
                    db.query(PlannedWorkout)
                    .filter(PlannedWorkout.plan_id == plan_id)
                    .filter(PlannedWorkout.date == activity_date)
                    .filter(PlannedWorkout.workout_type.notin_(["Rest", "Mobility"]))
                    .first()
                )

                # If workout already has a run, skip
                if planned and planned.actual_run:
                    print(f"Workout on {activity_date} already has a run, skipping")
                    continue

            # Create the run record
            run = ActualRun(
                planned_workout_id=planned.id if planned else None,
                garmin_activity_id=activity_id,
                distance=round(distance, 2),
                duration_seconds=duration,
                pace=pace,
                pace_seconds=pace_sec,
                avg_hr=activity.get("averageHR"),
                max_hr=activity.get("maxHR"),
                elevation_gain=round(activity.get("elevationGain", 0) * 3.28084, 1) if activity.get("elevationGain") else None,
                cadence=activity.get("averageRunningCadenceInStepsPerMinute"),
                calories=activity.get("calories"),
                start_lat=activity.get("startLatitude"),
                start_lon=activity.get("startLongitude"),
                started_at=self._parse_datetime(activity.get("startTimeLocal")),
                raw_data=activity,
            )

            db.add(run)
            db.commit()
            db.refresh(run)

            # Fetch weather for this run
            await self._fetch_weather_for_run(db, run)

            synced.append({
                "id": run.id,
                "date": activity_date.isoformat() if activity_date else None,
                "distance": run.distance,
                "pace": run.pace,
                "matched": planned.id if planned else None,
            })

            print(f"Synced: {run.distance}mi on {activity_date} -> {'matched to workout' if planned else 'unmatched'}")

        # Also sync sleep data for these dates
        await self.sync_sleep_data(db, plan_id, start_date, end_date)

        return synced

    async def sync_sleep_data(
        self,
        db: Session,
        plan_id: int,
        start_date: date,
        end_date: date,
    ):
        """Sync sleep and HRV data from Garmin for workouts in date range."""
        if not self.client:
            return

        # Get all workouts in the date range that don't have sleep or HRV data
        workouts = (
            db.query(PlannedWorkout)
            .filter(PlannedWorkout.plan_id == plan_id)
            .filter(PlannedWorkout.date >= start_date)
            .filter(PlannedWorkout.date <= end_date)
            .filter(
                (PlannedWorkout.sleep_hours.is_(None)) | (PlannedWorkout.hrv.is_(None))
            )
            .all()
        )

        print(f"Fetching sleep/HRV data for {len(workouts)} workouts")

        for workout in workouts:
            # Fetch sleep data if missing
            if workout.sleep_hours is None:
                try:
                    sleep_data = self.client.get_sleep_data(workout.date.isoformat())
                    if sleep_data and sleep_data.get("dailySleepDTO"):
                        daily = sleep_data["dailySleepDTO"]
                        sleep_seconds = daily.get("sleepTimeSeconds", 0)
                        if sleep_seconds > 0:
                            workout.sleep_hours = round(sleep_seconds / 3600, 1)
                            print(f"Sleep for {workout.date}: {workout.sleep_hours}h")
                except Exception as e:
                    print(f"Failed to get sleep for {workout.date}: {e}")

            # Fetch HRV data if missing
            if workout.hrv is None:
                try:
                    hrv_data = self.client.get_hrv_data(workout.date.isoformat())
                    if hrv_data and hrv_data.get("hrvSummary"):
                        summary = hrv_data["hrvSummary"]
                        last_night_avg = summary.get("lastNightAvg")
                        if last_night_avg:
                            workout.hrv = int(last_night_avg)
                            print(f"HRV for {workout.date}: {workout.hrv}ms")
                except Exception as e:
                    print(f"Failed to get HRV for {workout.date}: {e}")

            db.commit()

    async def _fetch_weather_for_run(self, db: Session, run: ActualRun):
        """Fetch and store weather data for a run."""
        if not run.start_lat or not run.start_lon or not run.started_at:
            print(f"Run {run.id} missing location/time data, skipping weather")
            return

        try:
            weather_data = await self.weather_service.get_historical_weather(
                lat=run.start_lat,
                lon=run.start_lon,
                dt=run.started_at,
            )

            weather = RunWeather(
                run_id=run.id,
                temperature=weather_data.get("temperature"),
                feels_like=weather_data.get("feels_like"),
                humidity=weather_data.get("humidity"),
                wind_speed=weather_data.get("wind_speed"),
                wind_direction=weather_data.get("wind_direction"),
                conditions=weather_data.get("conditions"),
                precipitation=weather_data.get("precipitation"),
            )

            db.add(weather)
            db.commit()
            print(f"Weather for run {run.id}: {weather.temperature}°F, {weather.conditions}")

        except Exception as e:
            print(f"Failed to fetch weather for run {run.id}: {e}")

    def _parse_date(self, date_str) -> Optional[date]:
        """Parse date from Garmin format."""
        if not date_str:
            return None
        try:
            if isinstance(date_str, str):
                clean = date_str.replace("Z", "").split("+")[0].split(".")[0]
                return datetime.fromisoformat(clean).date()
            return date_str.date() if hasattr(date_str, 'date') else None
        except:
            return None

    def _parse_datetime(self, date_str) -> Optional[datetime]:
        """Parse datetime from Garmin format."""
        if not date_str:
            return None
        try:
            if isinstance(date_str, str):
                clean = date_str.replace("Z", "").split("+")[0].split(".")[0]
                return datetime.fromisoformat(clean)
            return date_str
        except:
            return None
