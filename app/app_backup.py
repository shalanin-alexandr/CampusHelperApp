from flask import Flask, jsonify, render_template, request, redirect
import sys
import os
import json
import uuid
from datetime import datetime, timedelta

template_path = os.path.join(os.path.dirname(__file__), 'HTML')
app = Flask(__name__, template_folder=template_path)

app.secret_key = 'Poshalochka1488'  # можно удалить, если не используешь session

sys.path.append(os.path.abspath('./schedule'))

try:
    from schedule.excel_scraper import get_excel_schedule
    from schedule.doc_scraper import has_docx_url_changed, fetch_latest_docx_url, get_docx_schedule
    from schedule.schedule_merger import merge_schedules
    from grades.calculator import GradeTracker
    from notes.notes import (
        get_all_notes, create_note, delete_note,
        mark_note_as_done, edit_note
    )
    from sumarizer.compressor import compress_text, save_docx
    from events.users import authenticate, add_user
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

# 🔧 Настройки для событий
EVENTS_FILE = 'data/events.json'
UPLOAD_FOLDER = 'static/uploads'




def load_events():
    if not os.path.exists(EVENTS_FILE):
        return []
    with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_events(events):
    os.makedirs(os.path.dirname(EVENTS_FILE), exist_ok=True)
    with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

def save_event(title, description, date, content, image_file):
    events = load_events()
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filename = f"{uuid.uuid4().hex[:8]}_{image_file.filename}"
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    image_file.save(image_path)

    event = {
        "id": uuid.uuid4().hex[:8],
        "title": title,
        "description": description,
        "date": date,
        "content": content,
        "image": f"/static/uploads/{filename}"
    }
    events.append(event)
    save_events(events)

def delete_event(event_id):
    events = load_events()
    events = [e for e in events if e['id'] != event_id]
    save_events(events)


@app.route('/schedule')
def schedule_page():
    return render_template('schedule.html')


@app.route('/student')
def student_home():
    return render_template('student-home.html')


@app.route('/admin-panel/events')
def admin_events():
    events = load_events()
    return render_template('admin-events.html', events=events)

@app.route('/events')
def events_page():
    events = load_events()
    return render_template('events.html', events=events)


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = authenticate(username, password)
        if role == 'admin':
            return redirect('/admin-panel')
        error = "Неверный логин или пароль"
    return render_template('admin-login.html', error=error)

# 📋 Панель преподавателя
@app.route('/admin-panel')
def admin_panel():
    events = load_events()
    return render_template('admin-panel.html', events=events)

# ➕ Добавление события
@app.route('/admin-panel/create-event', methods=['GET', 'POST'])
def admin_create_event():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        content = request.form['content']
        image = request.files['image']
        save_event(title, description, date, content, image)
        return redirect('/admin-panel')
    return render_template('events_create.html')  # ← используем твой шаблон

# 🗑️ Удаление события
@app.route('/admin-panel/delete-event/<event_id>')
def admin_delete_event(event_id):
    delete_event(event_id)
    return redirect('/admin-panel')

# 🔍 Просмотр одного события
@app.route('/event/<event_id>')
def event_detail(event_id):
    events = load_events()
    event = next((e for e in events if e['id'] == event_id), None)
    return render_template('event_detail.html', event=event)

# 🧠 Компрессор
@app.route('/compressor')
def compressor_page():
    return render_template('compressor.html')

@app.route('/api/compress', methods=['POST'])
def api_compress():
    data = request.json
    text = data.get('text', '')
    filename = data.get('filename', 'summary')
    summary = compress_text(text)
    path = save_docx(summary, filename)
    return jsonify({"summary": summary, "file": path})

# 📝 Заметки
@app.route('/api/notes')
def api_get_notes():
    return jsonify(get_all_notes())

@app.route('/api/notes/create', methods=['POST'])
def api_create_note():
    data = request.json
    create_note(data['text'], data['datetime'], data.get('repeat', 'none'))
    return jsonify({"status": "created"})

@app.route('/api/notes/delete/<note_id>', methods=['POST'])
def api_delete_note(note_id):
    delete_note(note_id)
    return jsonify({"status": "deleted"})

@app.route('/api/notes/done/<note_id>', methods=['POST'])
def api_mark_done(note_id):
    mark_note_as_done(note_id)
    return jsonify({"status": "done"})

@app.route('/notes')
def notes_page():
    return render_template('notes.html')

# 📊 Оценки
tracker = GradeTracker()

@app.route('/grades')
def grades_page():
    return render_template('grades.html')

@app.route('/api/grades/add/<int:value>')
def add_grade(value):
    tracker.add_grade(value)
    return jsonify({
        "grades": tracker.grades,
        "average": tracker.get_average(),
        "count": tracker.get_count()
    })

@app.route('/api/grades/remove')
def remove_grade():
    tracker.remove_last()
    return jsonify({
        "grades": tracker.grades,
        "average": tracker.get_average(),
        "count": tracker.get_count()
    })

@app.route('/api/grades')
def get_grades():
    return jsonify({
        "grades": tracker.grades,
        "average": tracker.get_average(),
        "count": tracker.get_count()
    })

# 📅 Расписание
@app.route('/')
def index():
    return redirect('/admin-login')  # можно заменить на расписание, если нужно

@app.route('/api/schedule')
def get_schedule():
    EXCEL_URL = "http://..."
    DOC_PAGE_URL = "http://..."
    MY_GROUP = "РС02-24"

    weekday_map_eng_to_rus = {
        "Monday": "Понедельник", "Tuesday": "Вторник", "Wednesday": "Среда",
        "Thursday": "Четверг", "Friday": "Пятница", "Saturday": "Суббота", "Sunday": "Воскресенье"
    }

    excel_schedule = get_excel_schedule(EXCEL_URL, MY_GROUP)
    if not excel_schedule or not excel_schedule.get("schedule"):
        return jsonify([{"day": "Ошибка", "data": {"group": MY_GROUP, "schedule": [{"comment": "Ошибка загрузки расписания."}]}}])

    DOCX_URL = fetch_latest_docx_url(DOC_PAGE_URL)
    doc_schedule = {"group": MY_GROUP, "schedule": []}
    doc_updated_status = False

    if DOCX_URL:
        doc_updated_status = has_docx_url_changed(DOCX_URL)
        temp_doc_schedule = get_docx_schedule(MY_GROUP, DOC_PAGE_URL, doc_updated_status)
        if temp_doc_schedule and temp_doc_schedule.get("schedule") is not None:
            doc_schedule = temp_doc_schedule

    now = datetime.now()
    today_rus = weekday_map_eng_to_rus[now.strftime("%A")]

    tomorrow = now + timedelta(days=1)
    if tomorrow.weekday() == 6:
        tomorrow += timedelta(days=1)
    tomorrow_rus = weekday_map_eng_to_rus[tomorrow.strftime("%A")]

    parsed_day_from_doc = None
    if doc_schedule.get("schedule"):
        parsed_day_from_doc = doc_schedule["schedule"][0].get("day")

    target_days = [parsed_day_from_doc] if parsed_day_from_doc else (
        ["Суббота", "Понедельник"] if today_rus == "Суббота" else [tomorrow_rus]
    )

    all_schedules = []
    for target_day in target_days:
        filtered = {
            "group": excel_schedule["group"],
            "schedule": [
                p for p in excel_schedule["schedule"]
                if (p.get("day") or "").strip().lower() == target_day.strip().lower()
            ]
        }

        doc_schedule_for_target_day = {
            "group": doc_schedule["group"],
            "schedule": [
                p for p in doc_schedule.get("schedule", [])
                if (p.get("day") or "").strip().lower() == target_day.strip().lower()
            ]
        }

        final_schedule = merge_schedules(filtered, doc_schedule_for_target_day)

        if final_schedule.get("schedule"):
            all_schedules.append({
                "day": target_day,
                "data": final_schedule
            })

    if not all_schedules:
        return jsonify([{
            "day": "Нет данных",
            "data": {
                "group": MY_GROUP,
                "schedule": [{"comment": f"Нет пар на {', '.join(target_days)}."}]
            }
        }])

    return jsonify(all_schedules)

def print_banner():
    banner = r"""
   ____                                _    _       _             
  / ___|__ _ _ __ ___  ___ _ __   ___| | _| |_ ___| |__   ___ _ __ 
 | |   / _` | '__/ __|/ _ \ '_ \ / _ \ |/ / __/ __| '_ \ / _ \ '__|
 | |__| (_| | |  \__ \  __/ | | |  __/   <| || (__| | | |  __/ |   
  \____\__,_|_|  |___/\___|_| |_|\___|_|\_\\__\___|_| |_|\___|_|   

    Campus Helper Server is now running...
    """
    print(banner)

if __name__ == '__main__':
    print_banner()
    app.run(debug=True)



