from app.routers.plans import router as plans_router
from app.routers.workouts import router as workouts_router
from app.routers.runs import router as runs_router
from app.routers.notes import router as notes_router
from app.routers.sync import router as sync_router
from app.routers.stats import router as stats_router

__all__ = [
    "plans_router",
    "workouts_router",
    "runs_router",
    "notes_router",
    "sync_router",
    "stats_router",
]
