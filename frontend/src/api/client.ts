import axios from 'axios'

// Use VITE_API_URL for development, fall back to /api for production
const baseURL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface Workout {
  id: number
  plan_id: number
  week: number
  day_of_week: string
  date: string
  workout_type: string
  target_distance: number | null
  target_pace: string | null
  description: string | null
  fueling: string | null
  sleep_hours: number | null
  hrv: number | null
  actual_run: ActualRun | null
  note: RunNote | null
}

export interface ActualRun {
  id: number
  planned_workout_id: number | null
  garmin_activity_id: string | null
  distance: number
  duration_seconds: number
  pace: string
  pace_seconds: number
  avg_hr: number | null
  max_hr: number | null
  hr_zones: Record<string, number> | null
  elevation_gain: number | null
  cadence: number | null
  calories: number | null
  training_effect_aerobic: number | null
  training_effect_anaerobic: number | null
  vo2max: number | null
  start_lat: number | null
  start_lon: number | null
  started_at: string | null
  splits?: RunSplit[]
  weather?: RunWeather | null
}

export interface RunSplit {
  id: number
  split_number: number
  distance: number
  duration_seconds: number
  pace: string
  pace_seconds: number
  avg_hr: number | null
  elevation_gain: number | null
  cadence: number | null
}

export interface RunWeather {
  id: number
  temperature: number | null
  feels_like: number | null
  humidity: number | null
  wind_speed: number | null
  wind_direction: string | null
  conditions: string | null
  precipitation: number | null
}

export interface RunNote {
  id: number
  planned_workout_id: number
  content: string | null
  mood_rating: number | null
  effort_rating: number | null
  audio: string | null
  tags: string[] | null
  fueling_log: Array<{type: string; time?: string; brand?: string}> | null
  created_at: string
  updated_at: string
}

export interface Countdown {
  race_date: string
  race_name: string
  days_left: number
  weeks_left: number
  days_remainder: number
  target_pace: string | null
  target_time: string | null
}

// API functions
export const getWorkouts = (params?: { plan_id?: number; week?: number }) =>
  api.get<Workout[]>('/workouts/', { params })
export const updateWorkout = (id: number, data: Partial<Workout>) =>
  api.patch<Workout>(`/workouts/${id}`, data)

export const upsertNote = (workoutId: number, data: Partial<RunNote>) =>
  api.put<RunNote>(`/notes/workout/${workoutId}`, data)

export const getCountdown = (planId: number) =>
  api.get<Countdown>('/stats/countdown', { params: { plan_id: planId } })

export const garminStatus = () => api.get('/sync/garmin/status')
export const garminSync = (planId: number, startDate?: string, endDate?: string) =>
  api.post('/sync/garmin/activities', null, { params: { plan_id: planId, start_date: startDate, end_date: endDate } })

export default api
