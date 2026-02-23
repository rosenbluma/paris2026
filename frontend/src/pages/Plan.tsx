import { useState, useEffect, useRef } from 'react'
import { getWorkouts, getCountdown, garminStatus, garminSync, updateWorkout, upsertNote, type Workout, type Countdown } from '../api/client'

function formatDuration(seconds: number): string {
  const hrs = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export default function Plan() {
  const [workouts, setWorkouts] = useState<Workout[]>([])
  const [countdown, setCountdown] = useState<Countdown | null>(null)
  const [loading, setLoading] = useState(true)
  const [editingCell, setEditingCell] = useState<{ id: number; field: string } | null>(null)
  const [editValue, setEditValue] = useState('')
  const [garminConnected, setGarminConnected] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [syncMessage, setSyncMessage] = useState('')
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null)

  const planId = 1

  useEffect(() => {
    loadData()
    checkGarminStatus()
  }, [])

  useEffect(() => {
    if (editingCell && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [editingCell])

  const loadData = async () => {
    setLoading(true)
    try {
      const [workoutsRes, countdownRes] = await Promise.all([
        getWorkouts({ plan_id: planId }),
        getCountdown(planId),
      ])
      setWorkouts(workoutsRes.data)
      setCountdown(countdownRes.data)
    } catch (error) {
      console.error('Failed to load plan:', error)
    } finally {
      setLoading(false)
    }
  }

  const checkGarminStatus = async () => {
    try {
      const res = await garminStatus()
      setGarminConnected(res.data.status === 'connected')
    } catch {
      setGarminConnected(false)
    }
  }

  const handleSync = async () => {
    setSyncing(true)
    setSyncMessage('')
    try {
      const res = await garminSync(planId)
      const count = res.data.activities_synced
      setSyncMessage(count > 0 ? `${count} synced` : 'Up to date')
      await loadData()
    } catch {
      setSyncMessage('Failed')
    } finally {
      setSyncing(false)
    }
  }

  const startEdit = (id: number, field: string, currentValue: string | number | null) => {
    setEditingCell({ id, field })
    setEditValue(currentValue?.toString() || '')
  }

  const cancelEdit = () => {
    setEditingCell(null)
    setEditValue('')
  }

  const saveEdit = async () => {
    if (!editingCell) return

    const { id, field } = editingCell
    const workout = workouts.find(w => w.id === id)
    if (!workout) return

    // Update local state immediately
    setWorkouts(prev => prev.map(w => {
      if (w.id !== id) return w
      if (field === 'target_distance') {
        return { ...w, target_distance: editValue ? parseFloat(editValue) : null }
      } else if (field === 'workout_type') {
        return { ...w, workout_type: editValue }
      } else if (field === 'target_pace') {
        return { ...w, target_pace: editValue || null }
      } else if (field === 'fueling') {
        return { ...w, fueling: editValue || null }
      } else if (field === 'notes') {
        return { ...w, note: w.note ? { ...w.note, content: editValue || null } : { id: 0, planned_workout_id: id, content: editValue || null, mood_rating: null, effort_rating: null, audio: null, tags: null, fueling_log: null, created_at: '', updated_at: '' } }
      }
      return w
    }))

    setEditingCell(null)
    setEditValue('')

    // Save to backend in background
    try {
      if (field === 'notes') {
        await upsertNote(id, { content: editValue || null })
      } else {
        const updateData: Record<string, unknown> = {}
        if (field === 'target_distance') {
          updateData.target_distance = editValue ? parseFloat(editValue) : null
        } else if (field === 'workout_type') {
          updateData.workout_type = editValue
        } else if (field === 'target_pace') {
          updateData.target_pace = editValue || null
        } else if (field === 'fueling') {
          updateData.fueling = editValue || null
        }
        await updateWorkout(id, updateData)
      }
    } catch (error) {
      console.error('Failed to save:', error)
      loadData() // Reload on error
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      saveEdit()
    } else if (e.key === 'Escape') {
      cancelEdit()
    }
  }

  const getWeekWorkouts = (week: number) => workouts.filter((w) => w.week === week)

  if (loading) {
    return <div className="flex items-center justify-center min-h-[50vh]"><p className="text-gray-400">Loading...</p></div>
  }

  const weeks = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

  // Editable cell component
  const EditableCell = ({ workout, field, value, className = '', align = 'left' }: { workout: Workout; field: string; value: string | number | null; className?: string; align?: 'left' | 'right' }) => {
    const isEditing = editingCell?.id === workout.id && editingCell?.field === field
    const isEmpty = value === null || value === ''
    const displayValue = isEmpty ? '—' : (field === 'target_distance' ? `${value} mi` : value)

    if (isEditing) {
      return (
        <input
          ref={inputRef as React.RefObject<HTMLInputElement>}
          type={field === 'target_distance' ? 'number' : 'text'}
          step={field === 'target_distance' ? '0.1' : undefined}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onBlur={saveEdit}
          onKeyDown={handleKeyDown}
          className={`w-full bg-transparent outline-none ${align === 'right' ? 'text-right' : ''} ${className}`}
        />
      )
    }

    return (
      <span
        onClick={() => startEdit(workout.id, field, value)}
        className={`cursor-pointer hover:text-gray-900 ${isEmpty ? 'text-gray-300' : ''} ${className}`}
      >
        {displayValue}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">Paris Marathon · April 12, 2026</p>
          <p className="text-lg font-medium text-gray-800 mt-0.5">{countdown?.days_left} days to go</p>
        </div>

        <div className="flex items-center gap-3">
          {garminConnected && (
            <button
              onClick={handleSync}
              disabled={syncing}
              className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50"
            >
              {syncing ? 'Syncing...' : 'Sync Garmin'}
            </button>
          )}
          {syncMessage && <span className="text-xs text-gray-500">{syncMessage}</span>}
        </div>
      </div>

      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200 text-xs font-medium text-gray-500 uppercase tracking-wide">
              <th className="px-2 py-2 text-left w-8">Wk</th>
              <th className="px-2 py-2 text-left w-12">Date</th>
              <th className="px-2 py-2 text-left w-8">Day</th>
              <th className="px-2 py-2 text-left w-20">Type</th>
              <th className="px-2 py-2 text-right w-10">Dist</th>
              <th className="px-2 py-2 text-left w-16">Pace</th>
              <th className="px-2 py-2 text-left w-10">Fuel</th>
              <th className="px-2 py-2 text-left w-12 border-l border-gray-100">Start</th>
              <th className="px-2 py-2 text-right w-12">Actual</th>
              <th className="px-2 py-2 text-left w-14">Pace</th>
              <th className="px-2 py-2 text-right w-12">Time</th>
              <th className="px-2 py-2 text-right w-10">Elev</th>
              <th className="px-2 py-2 text-right w-12 whitespace-nowrap">HR</th>
              <th className="px-2 py-2 text-right w-8">Tmp</th>
              <th className="px-2 py-2 text-right w-12">Sleep</th>
              <th className="px-2 py-2 text-right w-10">HRV</th>
              <th className="px-2 py-2 text-center w-8">RPE</th>
              <th className="px-2 py-2 text-left w-16">Audio</th>
              <th className="px-2 py-2 text-left">Notes</th>
            </tr>
          </thead>
          <tbody>
            {weeks.map((week) => {
              const weekWorkouts = getWeekWorkouts(week)

              return weekWorkouts.map((workout, idx) => {
                const isCompleted = workout.actual_run !== null
                const isFirstInWeek = idx === 0
                const isRest = workout.workout_type === 'Rest'
                const isEditingNotes = editingCell?.id === workout.id && editingCell?.field === 'notes'

                return (
                  <tr
                    key={workout.id}
                    className="border-b border-gray-100 hover:bg-gray-50/50"
                  >
                    <td className="px-2 py-1 text-gray-400 text-xs">
                      {isFirstInWeek && week}
                    </td>
                    <td className="px-2 py-1 text-gray-600 text-xs whitespace-nowrap">{formatDate(workout.date)}</td>
                    <td className="px-2 py-1 text-gray-400 text-xs">{workout.day_of_week}</td>
                    <td className="px-2 py-1">
                      <select
                        value={workout.workout_type}
                        onChange={(e) => {
                          const newValue = e.target.value
                          setWorkouts(prev => prev.map(w => w.id === workout.id ? { ...w, workout_type: newValue } : w))
                          updateWorkout(workout.id, { workout_type: newValue }).catch(() => loadData())
                        }}
                        className="bg-transparent outline-none appearance-none cursor-pointer hover:text-gray-900 text-xs text-gray-700"
                      >
                        <option value="Rest">Rest</option>
                        <option value="Easy">Easy</option>
                        <option value="Recovery">Recovery</option>
                        <option value="Long">Long</option>
                        <option value="Shakeout">Shakeout</option>
                        <option value="Race">Race</option>
                      </select>
                    </td>
                    <td className="px-2 py-1 text-right text-xs whitespace-nowrap">
                      <EditableCell workout={workout} field="target_distance" value={workout.target_distance} className={isRest ? 'text-gray-300' : 'text-gray-700'} align="right" />
                    </td>
                    <td className="px-2 py-1 text-xs">
                      <EditableCell workout={workout} field="target_pace" value={workout.target_pace} className={isRest ? 'text-gray-300' : 'text-gray-500'} />
                    </td>
                    <td className="px-2 py-1 text-xs">
                      <EditableCell workout={workout} field="fueling" value={workout.fueling} className={isRest ? 'text-gray-300' : 'text-gray-500'} />
                    </td>

                    {/* Actual data */}
                    <td className="px-2 py-1 text-gray-600 text-xs border-l border-gray-100">
                      {isCompleted && workout.actual_run?.started_at
                        ? new Date(workout.actual_run.started_at).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }).toLowerCase().replace(' ', '')
                        : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-2 py-1 text-gray-700 text-xs text-right">
                      {isCompleted ? `${workout.actual_run?.distance.toFixed(1)}mi` : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-2 py-1 text-gray-600 text-xs">
                      {isCompleted ? workout.actual_run?.pace : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-2 py-1 text-gray-600 text-xs text-right">
                      {isCompleted ? formatDuration(workout.actual_run!.duration_seconds) : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-2 py-1 text-gray-600 text-xs text-right">
                      {isCompleted && workout.actual_run?.elevation_gain ? `${Math.round(workout.actual_run.elevation_gain)}` : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-2 py-1 text-gray-600 text-xs text-right">
                      {isCompleted && workout.actual_run?.avg_hr ? workout.actual_run.avg_hr : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-2 py-1 text-gray-600 text-xs text-right">
                      {isCompleted && workout.actual_run?.weather?.temperature ? `${Math.round(workout.actual_run.weather.temperature)}°` : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-2 py-1 text-gray-600 text-xs text-right whitespace-nowrap">
                      {workout.sleep_hours ? `${Math.floor(workout.sleep_hours)}h${Math.round((workout.sleep_hours % 1) * 60)}m` : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-2 py-1 text-gray-600 text-xs text-right">
                      {workout.hrv ? workout.hrv : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-2 py-1 text-center text-xs">
                      {isCompleted ? (
                        <select
                          value={workout.note?.effort_rating || ''}
                          onChange={(e) => {
                            const newValue = e.target.value ? parseInt(e.target.value) : null
                            setWorkouts(prev => prev.map(w => w.id === workout.id ? { ...w, note: w.note ? { ...w.note, effort_rating: newValue } : { id: 0, planned_workout_id: workout.id, content: null, mood_rating: null, effort_rating: newValue, audio: null, tags: null, fueling_log: null, created_at: '', updated_at: '' } } : w))
                            upsertNote(workout.id, { effort_rating: newValue }).catch(() => loadData())
                          }}
                          className="bg-transparent outline-none appearance-none cursor-pointer text-xs text-gray-600 text-center w-6"
                        >
                          <option value="">—</option>
                          {[1,2,3,4,5,6,7,8,9,10].map(n => <option key={n} value={n}>{n}</option>)}
                        </select>
                      ) : <span className="text-gray-300 text-xs">—</span>}
                    </td>
                    <td className="px-2 py-1 text-xs">
                      {isCompleted ? (
                        <select
                          value={workout.note?.audio || ''}
                          onChange={(e) => {
                            const newValue = e.target.value || null
                            setWorkouts(prev => prev.map(w => w.id === workout.id ? { ...w, note: w.note ? { ...w.note, audio: newValue } : { id: 0, planned_workout_id: workout.id, content: null, mood_rating: null, effort_rating: null, audio: newValue, tags: null, fueling_log: null, created_at: '', updated_at: '' } } : w))
                            upsertNote(workout.id, { audio: newValue }).catch(() => loadData())
                          }}
                          className="bg-transparent outline-none appearance-none cursor-pointer text-xs text-gray-600"
                        >
                          <option value="">—</option>
                          <option value="music">Music</option>
                          <option value="audiobook">Book</option>
                          <option value="conversation">Chat</option>
                          <option value="none">None</option>
                        </select>
                      ) : <span className="text-gray-300 text-xs">—</span>}
                    </td>
                    <td className="px-2 py-1">
                      {isEditingNotes ? (
                        <input
                          ref={inputRef as React.RefObject<HTMLInputElement>}
                          type="text"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          onBlur={saveEdit}
                          onKeyDown={handleKeyDown}
                          className="w-full bg-transparent outline-none text-xs text-gray-600"
                          placeholder="Add note..."
                        />
                      ) : (
                        <span
                          onClick={() => startEdit(workout.id, 'notes', workout.note?.content || '')}
                          className={`cursor-pointer hover:text-gray-900 text-xs ${workout.note?.content ? 'text-gray-600' : 'text-gray-300'}`}
                          title={workout.note?.content || 'Add note'}
                        >
                          {workout.note?.content || '—'}
                        </span>
                      )}
                    </td>
                  </tr>
                )
              })
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
