from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    group = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    notes = relationship("Note", back_populates="user")

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    note_datetime = Column(String(100), nullable=True)   # ← переименовано, чтобы не конфликтовать с datetime.utcnow
    repeat = Column(String(50), default="none")
    done = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notes")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    ext_id = Column(String(64), nullable=True, index=True)  # оригинальный id из JSON, если есть
    title = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)
    date = Column(String(100), nullable=True)
    content = Column(Text, nullable=True)
    image = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
