import json
import uuid
from datetime import datetime
import os

EVENTS_FILE = "events.json"


def load_events():
    if not os.path.exists(EVENTS_FILE):
        return []
    with open(EVENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_events(events):
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=4, ensure_ascii=False)

def create_event(title, description, date, image, content, created_by="admin"):
    events = load_events()
    new_event = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "description": description,
        "date": date,
        "image": image,
        "content": content,
        "created_by": created_by,
        "created_at": datetime.now().isoformat()
    }
    events.append(new_event)
    save_events(events)
    print(f"✅ Событие создано: {title} ({date})")


def get_sorted_events():
    events = load_events()
    return sorted(events, key=lambda e: e["date"])


def get_event_by_id(event_id):
    events = load_events()
    for event in events:
        if event["id"] == event_id:
            return event
    return None


def edit_event(event_id, title=None, description=None, date=None, image=None, content=None):
    events = load_events()
    for event in events:
        if event["id"] == event_id:
            if title: event["title"] = title
            if description: event["description"] = description
            if date: event["date"] = date
            if image: event["image"] = image
            if content: event["content"] = content
            print(f"✏️ Событие обновлено: {event['title']}")
            break
    else:
        print(f"⚠️ Событие с id {event_id} не найдено.")
    save_events(events)

def delete_event(event_id):
    events = load_events()
    events = [e for e in events if e["id"] != event_id]
    save_events(events)
    print(f"🗑️ Событие удалено: {event_id}")
