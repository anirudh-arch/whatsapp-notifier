from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import models, auth_utils
from database import get_db
from pydantic import BaseModel
import csv
import io

router = APIRouter(
    prefix="/contacts",
    tags=["contacts"]
)

# --- Pydantic Schemas ---
class ContactBase(BaseModel):
    name: str
    phone_number: str
    tags: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class ContactUpdate(ContactBase):
    name: Optional[str] = None
    phone_number: Optional[str] = None

class GroupBase(BaseModel):
    name: str

class GroupCreate(GroupBase):
    pass

class ContactOut(ContactBase):
    id: int
    class Config:
        from_attributes = True

class GroupOut(GroupBase):
    id: int
    class Config:
        from_attributes = True

# --- Contact Endpoints ---

@router.post("/", response_model=ContactOut)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth_utils.get_current_user)):
    db_contact = models.Contact(**contact.dict(), user_id=current_user.id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@router.get("/", response_model=List[ContactOut])
def read_contacts(db: Session = Depends(get_db), current_user: models.User = Depends(auth_utils.get_current_user)):
    return db.query(models.Contact).filter(models.Contact.user_id == current_user.id).all()

@router.put("/{contact_id}", response_model=ContactOut)
def update_contact(contact_id: int, contact_update: ContactUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth_utils.get_current_user)):
    db_contact = db.query(models.Contact).filter(models.Contact.id == contact_id, models.Contact.user_id == current_user.id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    for key, value in contact_update.dict(exclude_unset=True).items():
        setattr(db_contact, key, value)
    
    db.commit()
    db.refresh(db_contact)
    return db_contact

@router.delete("/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth_utils.get_current_user)):
    db_contact = db.query(models.Contact).filter(models.Contact.id == contact_id, models.Contact.user_id == current_user.id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(db_contact)
    db.commit()
    return {"detail": "Contact deleted"}

# --- Group Endpoints ---

@router.post("/groups", response_model=GroupOut)
def create_group(group: GroupCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth_utils.get_current_user)):
    db_group = models.Group(**group.dict(), user_id=current_user.id)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@router.get("/groups", response_model=List[GroupOut])
def read_groups(db: Session = Depends(get_db), current_user: models.User = Depends(auth_utils.get_current_user)):
    return db.query(models.Group).filter(models.Group.user_id == current_user.id).all()

@router.post("/groups/{group_id}/add-contact/{contact_id}")
def add_contact_to_group(group_id: int, contact_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth_utils.get_current_user)):
    db_group = db.query(models.Group).filter(models.Group.id == group_id, models.Group.user_id == current_user.id).first()
    db_contact = db.query(models.Contact).filter(models.Contact.id == contact_id, models.Contact.user_id == current_user.id).first()
    
    if not db_group or not db_contact:
        raise HTTPException(status_code=404, detail="Group or Contact not found")
    
    if db_contact not in db_group.contacts:
        db_group.contacts.append(db_contact)
        db.commit()
    
    return {"detail": "Contact added to group"}

@router.get("/groups/{group_id}/contacts", response_model=List[ContactOut])
def read_group_contacts(group_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth_utils.get_current_user)):
    db_group = db.query(models.Group).filter(models.Group.id == group_id, models.Group.user_id == current_user.id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    return db_group.contacts

@router.delete("/groups/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth_utils.get_current_user)):
    db_group = db.query(models.Group).filter(models.Group.id == group_id, models.Group.user_id == current_user.id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    db.delete(db_group)
    db.commit()
    return {"detail": "Group deleted"}

@router.post("/import")
async def import_contacts(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(auth_utils.get_current_user)):
    content = await file.read()
    try:
        decoded = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            decoded = content.decode('latin-1')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Invalid file encoding. Please upload a UTF-8 or Latin-1 encoded CSV.")
    
    reader = csv.DictReader(io.StringIO(decoded))

    
    contacts_to_create = []
    for row in reader:
        # Assuming CSV has headers: name, phone_number, tags
        name = row.get('name')
        phone_number = row.get('phone_number')
        tags = row.get('tags')
        
        if name and phone_number:
            new_contact = models.Contact(
                name=name,
                phone_number=phone_number,
                tags=tags,
                user_id=current_user.id
            )
            contacts_to_create.append(new_contact)
    
    if contacts_to_create:
        db.add_all(contacts_to_create)
        db.commit()
    
    return {"detail": f"Successfully imported {len(contacts_to_create)} contacts"}
