from fastapi import FastAPI, Request, Form, UploadFile
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import datetime, timedelta
from collections import OrderedDict
import os, sys

# 📦 Импортируем БД и модели
from app.database import SessionLocal
from app import models

# 📦 Импорты модулей (всё внутри app)
sys.path.append(str(Path(__file__).resolve().parent / "schedule"))
from app.schedule.excel_scraper import get_excel_schedule
from app.schedule.doc_scraper import (
    has_docx_url_changed,
    fetch_latest_docx_url,
    get_docx_schedule,
    get_available_replacement_days
)
from app.schedule.schedule_merger import merge_schedules, normalize_day

from app.grades.calculator import GradeTracker
from app.notes.notes import (
    get_all_notes,
    create_note,
    delete_note,
    mark_note_as_done
)
from app.sumarizer.compressor import summarize_text, read_txt, read_docx, save_docx


# 📁 Базовые настройки
BASE_DIR = Path(__file__).resolve().parent
HTML_DIR = BASE_DIR / "HTML"

app = FastAPI(debug=True)

# 📁 Вся статика (иконки и т.п.)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.mount("/html-static", StaticFiles(directory=HTML_DIR), name="html-static")
# 📁 HTML и CSS/JS шаблоны
templates = Jinja2Templates(directory=HTML_DIR)

tracker = GradeTracker()


# 📌 Зависимость для БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 📌 Главная страница → редирект на /admin-login
@app.get("/")
async def index():
    return RedirectResponse("/admin-login")


@app.get("/schedule")
async def schedule_page(request: Request):
    EXCEL_URL = "http://www.bobruisk.belstu.by/uploads/b1/s/8/648/basic/117/614/Raspisanie_uchebnyih_zanyatiy_na_2025-2026_uch.god_1_semestr.xlsx?t=1756801696"
    DOC_PAGE_URL = "http://www.bobruisk.belstu.by/dnevnoe-otdelenie/raspisanie-zanyatiy-i-zvonkov-zamenyi"
    MY_GROUP = "РС02-24"

    weekday_map_eng_to_rus = {
        "Monday": "Понедельник",
        "Tuesday": "Вторник",
        "Wednesday": "Среда",
        "Thursday": "Четверг",
        "Friday": "Пятница",
        "Saturday": "Суббота",
        "Sunday": "Воскресенье"
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


# 📌 Автоматическая генерация маршрутов для HTML файлов
# Например: events.html → /events
for html_file in HTML_DIR.glob("*.html"):
    route_name = "/" + html_file.stem

    async def _page(request: Request, file=html_file.name):
        return templates.TemplateResponse(file, {"request": request})

    app.get(route_name)(_page)


# 📌 Отдельный маршрут для Pomodoro (у тебя он был явно прописан)
@app.get("/pomodoro")
async def pomodoro_page(request: Request):
    return templates.TemplateResponse("pomodoro.html", {"request": request})

@app.get("/student")
async def student_page(request: Request):
    return templates.TemplateResponse("student-home.html", {"request": request})




# 📝 API заметок
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


# 📊 API оценок
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


# 📄 Компрессор (текстовый суммаризатор)
@app.get("/compressor")
async def compressor_page(request: Request):
    return templates.TemplateResponse("compressor.html", {"request": request})


@app.post("/api/compress")
async def compress(text: str = Form(None), filename: str = Form(...), file: UploadFile = None):
    if file:
        ext = file.filename.lower().split('.')[-1]
        content = await file.read()
        path = BASE_DIR / f"temp_upload.{ext}"
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

    return {"summary": summary, "file": str(saved_path)}
