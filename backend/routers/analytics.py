from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import models, auth_utils
from database import get_db
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)

class LogOut(BaseModel):
    id: int
    contact_name: str
    message_body: str
    timestamp: datetime
    status: str

    class Config:
        from_attributes = True

class StatsOut(BaseModel):
    total_messages: int
    success_count: int
    failed_count: int
    success_rate: float

@router.get("/logs", response_model=List[LogOut])
def get_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth_utils.get_current_user)):
    logs = db.query(models.MessageLog)\
        .filter(models.MessageLog.user_id == current_user.id)\
        .order_by(models.MessageLog.timestamp.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    # We want to include the contact name in the output
    results = []
    for log in logs:
        results.append({
            "id": log.id,
            "contact_name": log.contact.name if log.contact else "Unknown",
            "message_body": log.message_body,
            "timestamp": log.timestamp,
            "status": log.status
        })
    return results

@router.get("/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db), current_user: models.User = Depends(auth_utils.get_current_user)):
    total = db.query(models.MessageLog).filter(models.MessageLog.user_id == current_user.id).count()
    success = db.query(models.MessageLog).filter(models.MessageLog.user_id == current_user.id, models.MessageLog.status == "success").count()
    failed = total - success
    
    rate = (success / total * 100) if total > 0 else 0
    
    return {
        "total_messages": total,
        "success_count": success,
        "failed_count": failed,
        "success_rate": round(rate, 2)
    }
