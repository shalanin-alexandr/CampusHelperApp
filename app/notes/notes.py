# app/notes/notes.py
from sqlalchemy.orm import Session
from app.models import Note

def get_all_notes(db: Session, user_id: int):
    return db.query(Note).filter(Note.user_id == user_id).order_by(Note.created_at.desc()).all()

def create_note(db: Session, user_id: int, text: str, datetime_str: str = None, repeat: str = "none"):
    note = Note(
        text=text,
        note_datetime=datetime_str,
        repeat=repeat,
        user_id=user_id
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

def delete_note(db: Session, note_id: int, user_id: int):
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()
    if note:
        db.delete(note)
        db.commit()
        return True
    return False

def mark_note_as_done(db: Session, note_id: int, user_id: int):
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()
    if note:
        note.done = True
        db.commit()
        return True
    return False
