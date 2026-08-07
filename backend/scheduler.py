from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("SQLALCHEMY_DATABASE_URL", "sqlite:///./whatsapp_notifier.db")
job_store_url = db_url.replace("whatsapp_notifier.db", "jobs.sqlite")

jobstores = {
    "default": SQLAlchemyJobStore(url=job_store_url)
}

scheduler = AsyncIOScheduler(jobstores=jobstores)

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        print("Scheduler started.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler stopped.")
