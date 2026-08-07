from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from limiter_config import limiter

from sqlalchemy.orm import Session
from typing import List, Optional
import models, auth_utils, utils
from database import get_db, SessionLocal
from pydantic import BaseModel
try:
    import pywhatkit
except Exception:
    pywhatkit = None
import time
import asyncio
import json
from datetime import datetime
from websocket_manager import manager
from scheduler import scheduler

router = APIRouter(
    prefix="/messages",
    tags=["messages"]
)

class SendMessageRequest(BaseModel):
    template_id: int
    group_id: Optional[int] = None
    contact_ids: Optional[List[int]] = None
    scheduled_at: Optional[datetime] = None

async def dispatch_whatsapp_messages(user_id: int, template_body: str, contact_info: List[dict]):
    """
    Background task to send messages, log the results, and broadcast progress via WebSocket.
    """
    db = SessionLocal()
    try:
        for info in contact_info:
            final_msg = utils.parse_template(template_body, info)
            phone = info.get("phone_number")
            contact_id = info.get("id")
            
            status = "failed"
            if phone:
                try:
                    if pywhatkit is not None:
                        await asyncio.to_thread(
                            pywhatkit.sendwhatmsg_instantly,
                            phone_no=phone,
                            message=final_msg,
                            wait_time=15,
                            tab_close=True,
                            close_time=5
                        )
                        status = "success"
                    else:
                        print(f"Skipped WhatsApp send to {phone}: pywhatkit not available on cloud.")
                        status = "skipped"
                    
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"Failed to send to {phone}: {e}")
            
            # Create Log
            new_log = models.MessageLog(
                user_id=user_id,
                contact_id=contact_id,
                message_body=final_msg,
                status=status
            )
            db.add(new_log)
            db.commit()
            
            # Broadcast progress update
            message = {
                "contact_name": info.get("name"),
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
            await manager.broadcast_json(message)

    finally:
        db.close()

@router.post("/send")
@limiter.limit("2/minute")
async def send_messages(
    request: Request,
    req: SendMessageRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    template = db.query(models.Template).filter(
        models.Template.id == req.template_id, 
        models.Template.user_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    contacts_to_send = []
    
    if req.group_id:
        group = db.query(models.Group).filter(
            models.Group.id == req.group_id, 
            models.Group.user_id == current_user.id
        ).first()
        if group:
            contacts_to_send.extend(group.contacts)
            
    if req.contact_ids:
        specific_contacts = db.query(models.Contact).filter(
            models.Contact.id.in_(req.contact_ids), 
            models.Contact.user_id == current_user.id
        ).all()
        contacts_to_send.extend(specific_contacts)
    
    unique_contacts = {c.id: c for c in contacts_to_send}.values()
    
    if not unique_contacts:
        raise HTTPException(status_code=400, detail="No valid contacts found to send to")
    
    contact_info = [
        {"id": c.id, "name": c.name, "phone_number": c.phone_number, "tags": c.tags} 
        for c in unique_contacts
    ]
    
    if req.scheduled_at:
        # Schedule the task for later
        scheduler.add_job(
            dispatch_whatsapp_messages,
            'date',
            run_date=req.scheduled_at,
            args=[current_user.id, template.body, contact_info],
            misfire_grace_time=3600
        )
        return {"detail": f"Messaging task scheduled for {req.scheduled_at}. {len(unique_contacts)} contacts queued."}
    else:
        # Run immediately in background
        background_tasks.add_task(dispatch_whatsapp_messages, current_user.id, template.body, contact_info)
        return {"detail": f"Messaging task started for {len(unique_contacts)} contacts. Logs will be updated accordingly."}
