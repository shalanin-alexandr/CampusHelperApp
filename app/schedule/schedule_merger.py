from excel_scraper import get_excel_schedule, split_time_interval
import doc_scraper as ds
from doc_scraper import (
    get_docx_schedule,
    get_available_replacement_days,
    fetch_latest_docx_url,
    has_docx_url_changed
)
from datetime import datetime, timedelta
from collections import OrderedDict
import json
import os
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

def normalize_pair(pair):
    """
    Нормализует обозначение пары к базовому числу:
    '4' -> '4', '4/1' -> '4', '4лр' -> '4', '4.1' -> '4'
    Возвращает строку с цифрами или None.
    """
    if not pair:
        return None
    s = str(pair)
    m = re.search(r'(\d+)', s)
    return m.group(1) if m else None

def parse_pair_for_sort(pair):
    """
    Возвращает кортеж (base:int, sub:int) для сортировки:
    '4' -> (4,0), '4/1' -> (4,1), '4/2'->(4,2), иначе big.
    """
    if not pair:
        return (9999, 9999)
    s = str(pair)
    m = re.match(r'\s*(\d+)(?:\s*/\s*(\d+))?', s)
    if m:
        base = int(m.group(1))
        sub = int(m.group(2)) if m.group(2) else 0
        return (base, sub)
    # fallback: try to find first number
    m2 = re.search(r'(\d+)', s)
    if m2:
        return (int(m2.group(1)), 0)
    return (9999, 9999)

def is_pair_match(excel_pair, doc_pair):
    """
    Гибкое сравнение пар:
    - '4' == '4/1' == '4/2' == '4лр' (сравниваем по базовому номеру)
    - '4/1' соответствует '4' и '4/1'
    """
    if not excel_pair or not doc_pair:
        return False
    ex = normalize_pair(excel_pair)
    dc = normalize_pair(doc_pair)
    return (ex is not None and dc is not None and ex == dc)

def get_docx_schedule_from_doc(doc, group_name):
    """
    Вспомогательная функция: получает Document (python-docx) и парсит
    расписание так же, как это делает get_docx_schedule внутри doc_scraper.
    Используется как fallback, если мы имеем прямой URL к .docx.
    """
    try:
        full_schedule = {"group": group_name, "schedule": []}
        week_type = ds.get_week_type_from_docx(doc)
        full_schedule["week_type"] = week_type

        # Собираем список дней из абзацев
        day_labels = []
        for para in doc.paragraphs:
            text = para.text.strip().upper()
            match = re.search(r'(ПОНЕДЕЛЬНИК|ВТОРНИК|СРЕДА|ЧЕТВЕРГ|ПЯТНИЦА|СУББОТА|ВОСКРЕСЕНИЕ|ВОСКРЕСЕНЬЕ)', text)
            if match:
                day_labels.append(match.group(1).capitalize())

        # Привязка дней к таблицам
        for i, table in enumerate(doc.tables):
            if i < len(day_labels):
                day_label = day_labels[i]
            else:
                # резервный выбор дня — завтра (если воскресенье — следующая не-суббота)
                target_day = datetime.now() + timedelta(days=1)
                if target_day.weekday() == 6:
                    target_day += timedelta(days=1)
                day_label = weekday_map_eng_to_rus[target_day.weekday()]

            result = ds.parse_schedule_table(table, group_name, day_label)
            full_schedule["schedule"].extend(result["schedule"])

        if full_schedule["schedule"]:
            return full_schedule
        else:
            # возвращаем пустую структуру (чтобы было понятно, что группы нет)
            return full_schedule

    except Exception as e:
        print("❌ Ошибка при разборе docx-документа:", e)
        return None

def merge_schedules(excel_data, doc_data):
    merged = {
        "group": excel_data.get("group"),
        "schedule": []
    }

    replacements = doc_data.get("schedule", []) if doc_data else []
    week_type = doc_data.get("week_type") if doc_data else None

    # Применяем замены по каждой записи Excel
    for lesson in excel_data.get("schedule", []):
        pair_number = str(lesson.get("pair")).strip() if lesson.get("pair") else None
        day = lesson.get("day", "").strip()
        room = lesson.get("room", "")
        subject = lesson.get("subject", "")
        lesson_week_type = lesson.get("week_type")
        duration = lesson.get("duration")

        # week_type filtering (как было)
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
        time = lesson.get("time") if "/" in str(pair_number) else lesson.get("raw_time")

        if replacement and "to" in replacement:
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

    # Собираем set базовых пар, присутствующих в Excel (для данного дня)
    excel_base_pairs = set(
        (normalize_day(l.get("day")), normalize_pair(l.get("pair")))
        for l in excel_data.get("schedule", []) if l.get("pair")
    )

    # Добавляем замены, которых нет в Excel (например, добавленные пары)
    for r in replacements:
        if "pair" in r and "to" in r and r.get("day"):
            base_key = (normalize_day(r["day"]), normalize_pair(r["pair"]))
            # если базовая пара уже есть в Excel — пропускаем добавление отдельной записи
            if base_key in excel_base_pairs:
                continue

            time = None
            # если замена имеет формат "4/1" — пытаемся определить корректное время
            if "/" in str(r["pair"]):
                base_pair = str(r["pair"]).split("/")[0]
                try:
                    index = int(str(r["pair"]).split("/")[1])
                except:
                    index = None

                excel_time = next(
                    (l.get("raw_time") for l in excel_data.get("schedule", [])
                     if str(l.get("pair", "")).startswith(base_pair)
                     and normalize_day(l.get("day")) == normalize_day(r["day"])
                     and l.get("raw_time")),
                    None
                )
                if excel_time and index in (1,2):
                    first, second = split_time_interval(excel_time)
                    time = first if index == 1 else second
            else:
                # ищем время по базовой паре (если есть)
                time = next(
                    (l.get("raw_time") for l in excel_data.get("schedule", [])
                     if normalize_pair(l.get("pair")) == normalize_pair(r["pair"])
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

    # Опционально: сортируем расписание по паре (1,2,3,4/1,4/2,...)
    merged["schedule"] = sorted(
        merged["schedule"],
        key=lambda item: parse_pair_for_sort(item.get("pair"))
    )

    return merged


# ------------------ main (тестовый блок) ------------------
if __name__ == '__main__':
    EXCEL_URL = "http://www.bobruisk.belstu.by/uploads/b1/s/8/648/basic/117/614/Raspisanie_uchebnyih_zanyatiy_na_2025-2026_uch.god_1_semestr.xlsx?t=1756801696"
    DOC_PAGE_URL = "http://www.bobruisk.belstu.by/dnevnoe-otdelenie/raspisanie-zanyatiy-i-zvonkov-zamenyi"
    MY_GROUP = "РС02-23"

    # Получаем Excel-расписание
    excel_schedule = get_excel_schedule(EXCEL_URL, MY_GROUP)

    # Пытаемся получить ссылку и распарсить DOCX (обычный путь)
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
    else:
        # fallback: попробуем загрузить DOCX по последней сохранённой ссылке в кэше
        try:
            cache_path = ds.CACHE_FILE
            if os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    last_url = f.read().strip()
                if last_url:
                    print("⚠️ fetch_latest_docx_url вернул None — пытаюсь загрузить из кэше:", last_url)
                    try:
                        doc = ds.load_docx_from_url(last_url)
                        temp_doc_schedule = get_docx_schedule_from_doc(doc, MY_GROUP)
                        if temp_doc_schedule:
                            doc_schedule = temp_doc_schedule
                    except Exception as e:
                        print("❌ Ошибка при загрузке/парсинге DOCX по кешу:", e)
        except Exception as e:
            print("❌ Ошибка при чтении кеш-файла:", e)

    if not excel_schedule:
        print("❌ Ошибка при получении основного расписания.")
        exit()

    now = datetime.now()
    today_rus = weekday_map_eng_to_rus[now.strftime("%A")]

    if doc_schedule and doc_schedule.get("schedule"):
        all_days = get_available_replacement_days(doc_schedule)
        sorted_days = sorted(all_days, key=lambda d: 0 if normalize_day(d) == "суббота'".replace("'", "") else 1)
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
                p for p in (doc_schedule.get("schedule", []) if doc_schedule else [])
                if normalize_day(p.get("day")) == target_day_norm
            ]
        }

        final_schedule = merge_schedules(filtered_excel, filtered_doc)

        # Сортируем дополнительно по паре чтобы 4/1 и 4/2 шли рядом
        final_schedule["schedule"] = sorted(
            final_schedule["schedule"],
            key=lambda item: parse_pair_for_sort(item.get("pair"))
        )

        schedule_by_day[target_day] = final_schedule["schedule"]

    for day, schedule in schedule_by_day.items():
        print(f"\n📅 Финальное расписание на {day}:")
        print(json.dumps(schedule, indent=4, ensure_ascii=False))
