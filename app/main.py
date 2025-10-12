from fastapi import FastAPI, Request, Form, UploadFile
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, sys, uuid, json
from datetime import datetime, timedelta
from collections import OrderedDict


# 📦 Импорты модулей
sys.path.append(os.path.abspath('./schedule'))
from schedule.excel_scraper import get_excel_schedule
from schedule.doc_scraper import has_docx_url_changed, fetch_latest_docx_url, get_docx_schedule, get_available_replacement_days
from schedule.schedule_merger import merge_schedules, normalize_day
from grades.calculator import GradeTracker
from notes.notes import get_all_notes, create_note, delete_note, mark_note_as_done, edit_note
from events.users import authenticate, add_user
from sumarizer.compressor import summarize_text, read_txt, read_docx, save_docx



app = FastAPI(debug=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/html-static", StaticFiles(directory="HTML"), name="html-static")

templates = Jinja2Templates(directory="HTML")

EVENTS_FILE = 'data/events.json'
UPLOAD_FOLDER = 'static/uploads'
tracker = GradeTracker()



# 📁 Вспомогательные функции
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
    with open(image_path, "wb") as f:
        f.write(image_file.file.read())
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

# 📄 HTML-страницы

@app.get("/pomodoro")
async def pomodoro(request: Request):
    return templates.TemplateResponse("pomodoro.html", {"request": request})

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    path = f"generated/{filename}"
    if not os.path.exists(path):
        return JSONResponse({"error": "Файл не найден"}, status_code=404)
    return FileResponse(path, filename=filename, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@app.get("/")
async def index():
    return RedirectResponse("/admin-login")

@app.get("/schedule")
async def schedule_page(request: Request):
    EXCEL_URL = "http://www.bobruisk.belstu.by/uploads/b1/s/8/648/basic/117/614/Raspisanie_uchebnyih_zanyatiy_na_2025-2026_uch.god_1_semestr.xlsx?t=1756801696"
    DOC_PAGE_URL = "http://www.bobruisk.belstu.by/dnevnoe-otdelenie/raspisanie-zanyatiy-i-zvonkov-zamenyi"
    MY_GROUP = "РС02-24"

    weekday_map_eng_to_rus = {
        "Monday": "Понедельник", "Tuesday": "Вторник", "Wednesday": "Среда",
        "Thursday": "Четверг", "Friday": "Пятница", "Saturday": "Суббота", "Sunday": "Воскресенье"
    }

    excel_schedule = get_excel_schedule(EXCEL_URL, MY_GROUP)
    if not excel_schedule or not excel_schedule.get("schedule"):
        return templates.TemplateResponse("schedule.html", {
            "request": request,
            "schedule_by_day": {
                "Ошибка": [{"comment": "Ошибка загрузки расписания."}]
            }
        })

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

    from collections import OrderedDict

    if doc_schedule.get("schedule"):
        all_days = get_available_replacement_days(doc_schedule)
        sorted_days = sorted(all_days, key=lambda d: 0 if normalize_day(d) == "суббота" else 1)
        if today_rus == "Воскресенье":
            sorted_days = [d for d in sorted_days if normalize_day(d) != "суббота"]
        target_days = sorted_days
    else:
        target_days = ["Суббота", "Понедельник"] if today_rus == "Суббота" else [tomorrow_rus]


    schedule_by_day = OrderedDict()
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
        schedule_by_day[target_day] = final_schedule.get("schedule", [])

    if not any(schedule_by_day.values()):
        schedule_by_day = {
            ", ".join(target_days): [{"comment": f"Нет пар на {', '.join(target_days)}."}]
        }

    return templates.TemplateResponse("schedule.html", {
        "request": request,
        "schedule_by_day": schedule_by_day
    })




@app.get("/student")
async def student_home(request: Request):
    return templates.TemplateResponse("student-home.html", {"request": request})

@app.get("/admin-panel/events")
async def admin_events(request: Request):
    events = load_events()
    return templates.TemplateResponse("admin-events.html", {"request": request, "events": events})

@app.get("/events")
async def events_page(request: Request):
    events = load_events()
    return templates.TemplateResponse("events.html", {"request": request, "events": events})

@app.get("/admin-login")
async def admin_login_get(request: Request):
    return templates.TemplateResponse("admin-login.html", {"request": request, "error": None})

@app.post("/admin-login")
async def admin_login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    role = authenticate(username, password)
    if role == 'admin':
        return RedirectResponse("/admin-panel", status_code=302)
    return templates.TemplateResponse("admin-login.html", {"request": request, "error": "Неверный логин или пароль"})

@app.get("/admin-panel")
async def admin_panel(request: Request):
    events = load_events()
    return templates.TemplateResponse("admin-panel.html", {"request": request, "events": events})

@app.get("/admin-panel/create-event")
async def create_event_form(request: Request):
    return templates.TemplateResponse("events_create.html", {"request": request})

@app.post("/admin-panel/create-event")
async def create_event_post(
    title: str = Form(...),
    description: str = Form(...),
    date: str = Form(...),
    content: str = Form(...),
    image: UploadFile = Form(...)
):
    save_event(title, description, date, content, image)
    return RedirectResponse("/admin-panel", status_code=302)

@app.get("/admin-panel/delete-event/{event_id}")
async def delete_event_route(event_id: str):
    delete_event(event_id)
    return RedirectResponse("/admin-panel", status_code=302)

@app.get("/event/{event_id}")
async def event_detail(request: Request, event_id: str):
    events = load_events()
    event = next((e for e in events if e['id'] == event_id), None)
    return templates.TemplateResponse("event_detail.html", {"request": request, "event": event})

@app.get("/compressor")
async def compressor_page(request: Request):
    return templates.TemplateResponse("compressor.html", {"request": request})

@app.get("/tools", response_class=HTMLResponse)
async def tools_page(request: Request):
    return templates.TemplateResponse("tools.html", {"request": request})

# 📦 API
@app.post("/api/compress")
async def compress(text: str = Form(None), filename: str = Form(...), file: UploadFile = None):
    if file:
        ext = file.filename.lower().split('.')[-1]
        content = await file.read()
        path = f"temp_upload.{ext}"
        with open(path, "wb") as f:
            f.write(content)

        if ext == "txt":
            text = read_txt(path)
        elif ext == "docx":
            text = read_docx(path)
        else:
            return JSONResponse({"error": "Неподдерживаемый формат файла"}, status_code=400)

        os.remove(path)

    if not text or not text.strip():
        return JSONResponse({"error": "Пустой текст"}, status_code=400)

    summary = summarize_text(text)
    saved_path = save_docx(summary, filename)

    return {"summary": summary, "file": saved_path}

@app.get("/api/notes")
async def api_get_notes():
    return get_all_notes()

@app.post("/api/notes/create")
async def api_create_note(data: dict):
    create_note(data['text'], data['datetime'], data.get('repeat', 'none'))
    return {"status": "created"}

@app.post("/api/notes/delete/{note_id}")
async def api_delete_note(note_id: str):
    delete_note(note_id)
    return {"status": "deleted"}

@app.post("/api/notes/done/{note_id}")
async def api_mark_done(note_id: str):
    mark_note_as_done(note_id)
    return {"status": "done"}

@app.get("/notes")
async def notes_page(request: Request):
    return templates.TemplateResponse("notes.html", {"request": request})

@app.get("/grades")
async def grades_page(request: Request):
    return templates.TemplateResponse("grades.html", {"request": request})

@app.get("/api/grades")
async def get_grades():
    return {
        "grades": tracker.grades,
        "average": tracker.get_average(),
        "count": tracker.get_count()
    }

@app.get("/api/grades/add/{value}")
async def add_grade(value: int):
    tracker.add_grade(value)
    return get_grades()

@app.get("/api/grades/remove")
async def remove_grade():
    tracker.remove_last()
    return get_grades()

@app.get("/api/schedule")
async def get_schedule():
    EXCEL_URL = "http://..."
    DOC_PAGE_URL = "http://..."
    MY_GROUP = "РС02-24"

    weekday_map_eng_to_rus = {
        "Monday": "Понедельник", "Tuesday": "Вторник", "Wednesday": "Среда",
        "Thursday": "Четверг", "Friday": "Пятница", "Saturday": "Суббота", "Sunday": "Воскресенье"
    }

    excel_schedule = get_excel_schedule(EXCEL_URL, MY_GROUP)
    if not excel_schedule or not excel_schedule.get("schedule"):
        return JSONResponse(content=[{
        "day": "Ошибка",
        "data": {
        "group": MY_GROUP,
        "schedule": [{"comment": "Ошибка загрузки расписания."}]
    }
}])


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

    parsed_days_from_doc = sorted(set(
        p.get("day") for p in doc_schedule.get("schedule", [])
        if p.get("day")
    ))
    target_days = parsed_days_from_doc if parsed_days_from_doc else (
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
        return JSONResponse(content=[{
        "day": "Нет данных",
        "data": {
        "group": MY_GROUP,
        "schedule": [{"comment": f"Нет пар на {', '.join(target_days)}."}]
        }
    }])


    return JSONResponse(content=all_schedules)




