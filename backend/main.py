from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from app.core.config import settings

# ── Structured logging for production ─────────────────────────────────────
log_level = logging.DEBUG if settings.APP_ENV == "development" else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("nexus")

# ── Lazy DB initialisation (runs once, guarded by flag) ───────────────────
_db_initialised = False


def _init_db():
    """Create tables and run migrations exactly once per process."""
    global _db_initialised
    if _db_initialised:
        return
    from app.core.database import engine, Base, ensure_user_email_columns, ensure_whatsapp_tables
    from app.models import *  # noqa: F401 — register all SQLAlchemy models

    logger.info("Initialising database tables …")
    Base.metadata.create_all(bind=engine)
    ensure_user_email_columns()
    ensure_whatsapp_tables()
    _db_initialised = True
    logger.info("Database initialisation complete.")


# ── FastAPI application ───────────────────────────────────────────────────
app = FastAPI(
    title="AI Work Operating System API",
    description="Backend API foundation and AI Agent tool layer for project management.",
    version="2.0.0",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
)


# ── Startup event — single-fire DB init ───────────────────────────────────
@app.on_event("startup")
def on_startup():
    _init_db()


# ── CORS Middleware ───────────────────────────────────────────────────────
# Build the list from FRONTEND_URL (set via env on Render).
# Always include localhost variants for local development.
allowed_origins = [
    settings.FRONTEND_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
# Strip empty/blank values and deduplicate
allowed_origins = list({o.rstrip("/") for o in allowed_origins if o and o.strip()})

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Exception Handler ─────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."}
    )


# ── Import & register routers ────────────────────────────────────────────
from app.tools import *   # noqa: F401,E402 — Register tool definitions
from app.api.routes import (  # noqa: E402
    auth, users, teams, projects, tasks, blockers,
    activities, notifications, ai, meetings, emails,
    chat, webhooks, whatsapp,
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(teams.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(blockers.router, prefix="/api")
app.include_router(activities.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(meetings.router, prefix="/api")
app.include_router(emails.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(whatsapp.router, prefix="/api")


# ── Health endpoint (used by Render health checks) ────────────────────────
@app.get("/api/health", tags=["Health"])
def health_check():
    db_type = "unknown"
    try:
        db_type = settings.DATABASE_URL.split("://")[0].replace("postgres", "postgresql")
    except Exception:
        pass
    return {
        "status": "healthy",
        "env": settings.APP_ENV,
        "database": db_type,
        "ai_agent": "ready"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
