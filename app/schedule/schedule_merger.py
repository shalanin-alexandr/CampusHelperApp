from excel_scraper import get_excel_schedule, split_time_interval
from doc_scraper import (
    get_docx_schedule,
    get_available_replacement_days,
    fetch_latest_docx_url,
    has_docx_url_changed
)
from datetime import datetime, timedelta
from collections import OrderedDict
import json

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

def is_pair_match(excel_pair, doc_pair):
    if not excel_pair or not doc_pair:
        return False
    return str(excel_pair).strip() == str(doc_pair).strip()

def merge_schedules(excel_data, doc_data):
    merged = {
        "group": excel_data["group"],
        "schedule": []
    }

    replacements = doc_data.get("schedule", []) if doc_data else []
    week_type = doc_data.get("week_type")

    for lesson in excel_data["schedule"]:
        pair_number = str(lesson.get("pair")).strip() if lesson.get("pair") else None
        day = lesson.get("day", "").strip()
        room = lesson.get("room", "")
        subject = lesson.get("subject", "")
        lesson_week_type = lesson.get("week_type")
        duration = lesson.get("duration")

        if lesson_week_type and week_type and lesson_week_type != week_type:
            continue

        if duration == 1 and lesson_week_type == "upper" and week_type == "lower":
            continue

        replacement = next(
            (r for r in replacements
             if is_pair_match(pair_number, r.get("pair"))
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
            if not has_second and duration == 2:
                display_pair = pair_number.split("/")[0]
            elif duration == 1:
                display_pair = pair_number

        # ⏰ Выбираем правильное время
        time = lesson.get("time") if "/" in str(pair_number) else lesson.get("raw_time")

        if replacement and "to" in replacement:
            print(f"🔁 Замена на {day}, пара {pair_number}: {subject} → {replacement['to'].get('subject')}")
            merged["schedule"].append({
                "day": day,
                "time": time,
                "pair": replacement.get("pair", display_pair),
                "room": replacement.get("room", room),
                "subject": replacement["to"].get("subject") or subject,
                "replaced_subject": subject
            })
        else:
            merged["schedule"].append({
                "day": day,
                "time": time,
                "pair": display_pair,
                "room": room,
                "subject": subject
            })

    excel_pairs = set((normalize_day(l["day"]), l["pair"]) for l in excel_data["schedule"] if l.get("pair"))

    for r in replacements:
        if "pair" in r and "to" in r and r.get("day"):
            key = (normalize_day(r["day"]), r["pair"])
            if key not in excel_pairs:
                time = None
                if "/" in r["pair"]:
                    base_pair = r["pair"].split("/")[0]
                    index = int(r["pair"].split("/")[1])
                    excel_time = next(
                        (l.get("raw_time") for l in excel_data["schedule"]
                        if str(l.get("pair", "")).startswith(base_pair)
                        and normalize_day(l.get("day")) == normalize_day(r["day"])
                        and l.get("raw_time")),
                        None
                    )

                    if excel_time:
                        first, second = split_time_interval(excel_time)
                        time = first if index == 1 else second
                else:
                    time = next(
                        (l.get("raw_time") for l in excel_data["schedule"]
                        if str(l.get("pair", "")).strip() == r["pair"].strip()
                        and normalize_day(l.get("day")) == normalize_day(r["day"])
                        and l.get("raw_time")),
                        None
                    )

                merged["schedule"].append({
                    "day": r["day"],
                    "time": time,
                    "pair": r["pair"],
                    "room": r.get("room", ""),
                    "subject": r["to"].get("subject", ""),
                    "replaced_subject": None
                })

        if "comment" in r:
            merged["schedule"].append({"comment": r["comment"]})

    return merged

if __name__ == '__main__':
    EXCEL_URL = "http://www.bobruisk.belstu.by/uploads/b1/s/8/648/basic/117/614/Raspisanie_uchebnyih_zanyatiy_na_2025-2026_uch.god_1_semestr.xlsx?t=1756801696"
    DOC_PAGE_URL = "http://www.bobruisk.belstu.by/dnevnoe-otdelenie/raspisanie-zanyatiy-i-zvonков-zamenyi"
    MY_GROUP = "РС02-24"

    excel_schedule = get_excel_schedule(EXCEL_URL, MY_GROUP)

    DOCX_URL = fetch_latest_docx_url(DOC_PAGE_URL)
    doc_schedule = None
    doc_updated = False

    if DOCX_URL:
        doc_updated = has_docx_url_changed(DOCX_URL)
        print(f"🔄 Обнаружена новая ссылка на замены: {doc_updated}")
        temp_doc_schedule = get_docx_schedule(MY_GROUP, DOC_PAGE_URL)
        if temp_doc_schedule:
            doc_schedule = temp_doc_schedule
        else:
            print("❌ doc_scraper вернул None или пустые данные.")

    if not excel_schedule:
        print("❌ Ошибка при получении основного расписания.")
        exit()

    now = datetime.now()
    today_rus = weekday_map_eng_to_rus[now.strftime("%A")]

    if doc_schedule and doc_schedule.get("schedule"):
        all_days = get_available_replacement_days(doc_schedule)
        sorted_days = sorted(all_days, key=lambda d: 0 if normalize_day(d) == "суббота" else 1)
        if today_rus == "Воскресенье":
            sorted_days = [d for d in sorted_days if normalize_day(d) != "суббота"]
    else:
        tomorrow = now + timedelta(days=1)
        if tomorrow.weekday() == 6:
            tomorrow += timedelta(days=1)
        tomorrow_rus = weekday_map_eng_to_rus[tomorrow.strftime("%A")]
        sorted_days = ["Суббота", "Понедельник"] if today_rus == "Суббота" else [tomorrow_rus]

    print(f"\n📎 Ссылка на замены: {DOCX_URL}")
    print(f"🔍 Замены обновились: {doc_updated}")
    print(f"📅 Сегодня: {today_rus}")
    print(f"🎯 Целевые дни для отображения: {sorted_days}")

    schedule_by_day = OrderedDict()

    for target_day in sorted_days:
        target_day_norm = normalize_day(target_day)
        filtered_excel = {
            "group": excel_schedule["group"],
            "schedule": [
                p for p in excel_schedule["schedule"]
                if normalize_day(p.get("day")) == target_day_norm
            ]
        }

        filtered_doc = {
            "group": doc_schedule["group"] if doc_schedule else MY_GROUP,
            "schedule": [
                p for p in doc_schedule.get("schedule", []) if doc_schedule
                and normalize_day(p.get("day")) == target_day_norm
            ]
        }

        final_schedule = merge_schedules(filtered_excel, filtered_doc)
        schedule_by_day[target_day] = final_schedule["schedule"]

    for day, schedule in schedule_by_day.items():
        print(f"\n📅 Финальное расписание на {day}:")
        print(json.dumps(schedule, indent=4, ensure_ascii=False))
