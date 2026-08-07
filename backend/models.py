from sqlalchemy import Column, Integer, String, ForeignKey, Table, Text, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

# Association table for Many-to-Many relationship between Contact and Group
contact_group_association = Table(
    "contact_group_association",
    Base.metadata,
    Column("contact_id", Integer, ForeignKey("contacts.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    contacts = relationship("Contact", back_populates="owner")
    groups = relationship("Group", back_populates="owner")
    templates = relationship("Template", back_populates="owner")
    logs = relationship("MessageLog", back_populates="owner")

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    phone_number = Column(String)
    tags = Column(String)

    owner = relationship("User", back_populates="contacts")
    groups = relationship("Group", secondary=contact_group_association, back_populates="contacts")
    logs = relationship("MessageLog", back_populates="contact")

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)

    owner = relationship("User", back_populates="groups")
    contacts = relationship("Contact", secondary=contact_group_association, back_populates="groups")

class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    body = Column(Text)

    owner = relationship("User", back_populates="templates")

class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    message_body = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String) # 'success', 'failed'

    owner = relationship("User", back_populates="logs")
    contact = relationship("Contact", back_populates="logs")
