import json
import uuid
from datetime import datetime, timedelta
import os

NOTES_FILE = "notes.json"


def load_notes():
    if not os.path.exists(NOTES_FILE):
        return []
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_notes(notes):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=4, ensure_ascii=False)


def create_note(text, remind_at, repeat="none"):
    notes = load_notes()
    new_note = {
        "id": str(uuid.uuid4())[:8],
        "text": text,
        "datetime": remind_at,
        "repeat": repeat,  
        "created_at": datetime.now().isoformat(),
        "status": "pending"
    }
    notes.append(new_note)
    save_notes(notes)
    print(f"✅ Заметка создана: {new_note['text']} (напомнить в {remind_at}, повтор: {repeat})")


def get_all_notes():
    return load_notes()


def get_due_notes(current_time=None):
    if current_time is None:
        current_time = datetime.now().isoformat()
    notes = load_notes()
    due = []
    for note in notes:
        if note["status"] == "pending" and note["datetime"] <= current_time:
            due.append(note)
    return due


def get_next_datetime(note):
    dt = datetime.fromisoformat(note["datetime"])
    repeat = note.get("repeat", "none")
    if repeat == "daily":
        return dt + timedelta(days=1)
    elif repeat == "weekly":
        return dt + timedelta(weeks=1)
    elif repeat == "weekdays":
        next_day = dt + timedelta(days=1)
        while next_day.weekday() >= 5:  
            next_day += timedelta(days=1)
        return next_day
    else:
        return None


def mark_note_as_done(note_id):
    notes = load_notes()
    for note in notes:
        if note["id"] == note_id:
            note["status"] = "done"
            print(f"☑️ Заметка выполнена: {note['text']}")
            break
    save_notes(notes)


def delete_note(note_id):
    notes = load_notes()
    notes = [note for note in notes if note["id"] != note_id]
    save_notes(notes)
    print(f"🗑️ Заметка удалена: {note_id}")


def edit_note(note_id, new_text=None, new_datetime=None, new_repeat=None):
    notes = load_notes()
    for note in notes:
        if note["id"] == note_id:
            if new_text:
                note["text"] = new_text
            if new_datetime:
                note["datetime"] = new_datetime
            if new_repeat:
                note["repeat"] = new_repeat
            print(f"✏️ Заметка обновлена: {note}")
            break
    else:
        print(f"⚠️ Заметка с id {note_id} не найдена.")
    save_notes(notes)




def check_and_notify():
    now = datetime.now().isoformat()
    notes = load_notes()
    updated = False

    for note in notes:
        if note["status"] == "pending" and note["datetime"] <= now:
            print(f"🔔 Напоминание: {note['text']} (создано {note['created_at']})")

            next_dt = get_next_datetime(note)
            if next_dt:
                create_note(note["text"], next_dt.isoformat(), note["repeat"])

            note["status"] = "done"
            updated = True

    if updated:
        save_notes(notes)
