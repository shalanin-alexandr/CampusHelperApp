from excel_scraper import get_excel_schedule
from doc_scraper import (
    get_docx_schedule,
    get_available_replacement_days,
    fetch_latest_docx_url,
    has_docx_url_changed
)
from datetime import datetime, timedelta
import json
import re

weekday_map_eng_to_rus = {
    "Monday": "Понедельник",
    "Tuesday": "Вторник",
    "Wednesday": "Среда",
    "Thursday": "Четверг",
    "Friday": "Пятница",
    "Saturday": "Суббота",
    "Sunday": "Воскресенье"
}

def normalize_day(day):
    return day.strip().lower().replace("ё", "е") if isinstance(day, str) else ""

def normalize_pair(p):
    return str(p).split("/")[0].strip() if p else ""

def merge_schedules(excel_data, doc_data):
    merged = {
        "group": excel_data["group"],
        "schedule": []
    }

    replacements = doc_data.get("schedule", [])

    for lesson in excel_data["schedule"]:
        pair_number = str(lesson.get("pair")).strip() if lesson.get("pair") else None
        day = lesson.get("day", "").strip()
        time = lesson.get("time")
        room = lesson.get("room", "")
        subject = lesson.get("subject", "")
        teacher = lesson.get("teacher", "")

        replacement = next(
            (r for r in replacements
             if normalize_pair(r.get("pair")) == normalize_pair(pair_number)
             and normalize_day(r.get("day")) == normalize_day(day)),
            None
        )

        display_pair = pair_number
        if pair_number and pair_number.endswith("/1"):
            has_second = any(
                str(p.get("pair", "")).startswith(pair_number.split("/")[0] + "/2")
                and normalize_day(p.get("day")) == normalize_day(day)
                for p in excel_data["schedule"]
            )
            if not has_second:
                display_pair = pair_number.split("/")[0]

        if replacement and "to" in replacement:
            print(f"🔁 Замена на {day}, пара {pair_number}: {subject} → {replacement['to'].get('subject')}")
            merged["schedule"].append({
                "day": day,
                "time": time,
                "pair": display_pair,
                "room": replacement.get("room", room),
                "subject": replacement["to"].get("subject") or subject,
                "teacher": replacement["to"].get("teacher") or teacher,
                "replaced_subject": subject,
                "replaced_teacher": teacher
            })
        else:
            merged["schedule"].append({
                "day": day,
                "time": time,
                "pair": display_pair,
                "room": room,
                "subject": subject,
                "teacher": teacher
            })

    for r in replacements:
        if "comment" in r:
            merged["schedule"].append({"comment": r["comment"]})

    return merged

if __name__ == '__main__':
    EXCEL_URL = "http://www.bobruisk.belstu.by/uploads/b1/s/8/648/basic/117/614/Raspisanie_uchebnyih_zanyatiy_na_2025-2026_uch.god_1_semestr.xlsx?t=1756801696"
    DOC_PAGE_URL = "http://www.bobruisk.belstu.by/dnevnoe-otdelenie/raspisanie-zanyatiy-i-zvonkov-zamenyi"
    MY_GROUP = "РС02-24"

    excel_schedule = get_excel_schedule(EXCEL_URL, MY_GROUP)

    DOCX_URL = fetch_latest_docx_url(DOC_PAGE_URL)
    if not DOCX_URL:
        print("❌ Не удалось получить ссылку на замены. Вывожу обычное расписание.")
        doc_updated = False
        doc_schedule = {"group": MY_GROUP, "schedule": []}
    else:
        doc_updated = has_docx_url_changed(DOCX_URL)
        if doc_updated:
            print("🔄 Обнаружена новая ссылка на замены.")
            doc_schedule = get_docx_schedule(MY_GROUP, DOC_PAGE_URL)
        else:
            print("ℹ️ Ссылка на замену не изменилась — замены не обновились.")
            doc_schedule = get_docx_schedule(MY_GROUP, DOC_PAGE_URL)

    if not excel_schedule:
        print("❌ Ошибка при получении основного расписания.")
        exit()

    now = datetime.now()
    today_rus = weekday_map_eng_to_rus[now.strftime("%A")]


    tomorrow = now + timedelta(days=1)
    if tomorrow.weekday() == 6:  # воскресенье
        tomorrow += timedelta(days=1)
    tomorrow_rus = weekday_map_eng_to_rus[tomorrow.strftime("%A")]


    if today_rus == "Суббота":
        target_days = ["Суббота", "Понедельник"]
    elif doc_updated:
        target_days = [tomorrow_rus]
    else:
        target_days = [today_rus]

    print(f"\n📎 Ссылка на замены: {DOCX_URL}")
    print(f"🔍 Замены обновились: {doc_updated}")
    print(f"📅 Сегодня: {today_rus}, Завтра: {tomorrow_rus}")
    print(f"🎯 Целевые дни для отображения: {target_days}")

    for target_day in target_days:
        target_day_norm = normalize_day(target_day)
        filtered = {
            "group": excel_schedule["group"],
            "schedule": [
                p for p in excel_schedule["schedule"]
                if normalize_day(p.get("day")) == target_day_norm
            ]
        }
        final_schedule = merge_schedules(filtered, doc_schedule)
        print(f"\n📅 Финальное расписание на {target_day}:")
        print(json.dumps(final_schedule, indent=4, ensure_ascii=False))
