from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import models, auth_utils
from database import get_db
from pydantic import BaseModel

router = APIRouter(
    prefix="/templates",
    tags=["templates"]
)

class TemplateBase(BaseModel):
    title: str
    body: str

class TemplateCreate(TemplateBase):
    pass

class TemplateUpdate(TemplateBase):
    title: Optional[str] = None
    body: Optional[str] = None

class TemplateOut(TemplateBase):
    id: int
    class Config:
        from_attributes = True

@router.post("/", response_model=TemplateOut)
def create_template(template: TemplateCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth_utils.get_current_user)):
    db_template = models.Template(**template.dict(), user_id=current_user.id)
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/", response_model=List[TemplateOut])
def read_templates(db: Session = Depends(get_db), current_user: models.User = Depends(auth_utils.get_current_user)):
    return db.query(models.Template).filter(models.Template.user_id == current_user.id).all()

@router.put("/{template_id}", response_model=TemplateOut)
def update_template(template_id: int, template_update: TemplateUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth_utils.get_current_user)):
    db_template = db.query(models.Template).filter(models.Template.id == template_id, models.Template.user_id == current_user.id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    for key, value in template_update.dict(exclude_unset=True).items():
        setattr(db_template, key, value)
    
    db.commit()
    db.refresh(db_template)
    return db_template

@router.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth_utils.get_current_user)):
    db_template = db.query(models.Template).filter(models.Template.id == template_id, models.Template.user_id == current_user.id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(db_template)
    db.commit()
    return {"detail": "Template deleted"}
