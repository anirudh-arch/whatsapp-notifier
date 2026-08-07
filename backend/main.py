from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import engine, Base
import models
from routers import auth, contacts, templates, messages, analytics, ws
from scheduler import start_scheduler, stop_scheduler

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from limiter_config import limiter

# Create all tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="WhatsApp Campaign Manager API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://whatsapp-notifier-ten.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")

@app.get("/api/health")
def health_check():
    return {"status": "ok"}
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)



@app.on_event("startup")
async def startup_event():
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()

# Configure CORS
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://127.0.0.1:8000,http://localhost:8000",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(contacts.router)
app.include_router(templates.router)
app.include_router(messages.router)
app.include_router(analytics.router)
app.include_router(ws.router)

# Mount Static Files (Frontend)
frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")





