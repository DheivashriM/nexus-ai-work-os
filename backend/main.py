from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.database import engine, Base, ensure_user_email_columns, ensure_whatsapp_tables
from app.models import *  # Ensure all SQLAlchemy models are registered
from app.tools import *   # Register tool definitions
from app.api.routes import auth, users, teams, projects, tasks, blockers, activities, notifications, ai, meetings, emails, chat, webhooks, whatsapp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_workspace")

# Create database tables automatically
Base.metadata.create_all(bind=engine)
ensure_user_email_columns()
ensure_whatsapp_tables()

app = FastAPI(
    title="AI Work Operating System API",
    description="Backend API foundation and AI Agent tool layer for project management.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware (Production: restrict to FRONTEND_URL; Dev: allow localhost)
allowed_origins = [
    settings.FRONTEND_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."}
    )

# Include Routers
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

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "env": settings.APP_ENV,
        "database": settings.DATABASE_URL.split("://")[0],
        "ai_agent": "ready"
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

