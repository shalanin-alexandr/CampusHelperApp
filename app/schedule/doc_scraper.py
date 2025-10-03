import requests
import io
import re
import os
from docx import Document
from datetime import datetime
import json

weekday_map = {
    0: "Понедельник",
    1: "Вторник",
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
    5: "Суббота",
    6: "Воскресенье"
}

def normalize_day(day):
    return day.strip().lower().replace("ё", "е") if isinstance(day, str) else ""

def normalize_group(g):
    return re.sub(r"\W+", "", g.strip().lower()) if isinstance(g, str) else ""

def fetch_latest_docx_url(page_url):
    try:
        response = requests.get(page_url)
        response.raise_for_status()
        html = response.text

        match = re.search(r'href="([^"]*Zamena_SAYT\.docx[^"]*)"', html)
        if match:
            return "http://www.bobruisk.belstu.by" + match.group(1)
        else:
            print("❌ Не удалось найти ссылку на DOCX.")
            return None
    except Exception as e:
        print(f"❌ Ошибка при получении ссылки: {e}")
        return None

def has_docx_url_changed(new_url, cache_file="last_docx_url.txt"):
    try:
        with open(cache_file, "r") as f:
            old_url = f.read().strip()
    except FileNotFoundError:
        old_url = ""

    if new_url != old_url:
        with open(cache_file, "w") as f:
            f.write(new_url)
        return True
    return False

def load_docx_from_url(url):
    response = requests.get(url)
    response.raise_for_status()
    return Document(io.BytesIO(response.content))

def parse_schedule_table(table, target_group, day_label):
    schedule_data = {
        "group": target_group,
        "schedule": []
    }

    current_group = None

    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]

        if not any(cells):
            continue

        if len(cells) == 2 and cells[0] and cells[1]:
            group = cells[0]
            comment = cells[1]
            if normalize_group(group) == normalize_group(target_group):
                schedule_data["schedule"].append({
                    "day": day_label,
                    "comment": comment
                })
            continue

        if cells[0] and not cells[0].startswith("-"):
            current_group = cells[0]

        if normalize_group(current_group) != normalize_group(target_group):
            continue

        try:
            pair_number = cells[1] if len(cells) > 1 else None
            room = cells[2] if len(cells) > 2 else None
            subject_to = cells[3] if len(cells) > 3 else None
            teacher_to = cells[4] if len(cells) > 4 else None
            subject_from = cells[5] if len(cells) > 5 else None
            teacher_from = cells[7] if len(cells) > 6 else None

            schedule_data["schedule"].append({
                "day": day_label,
                "pair": str(pair_number).strip() if pair_number else None,
                "room": room,
                "from": {
                    "subject": subject_from,
                    "teacher": teacher_from
                },
                "to": {
                    "subject": subject_to,
                    "teacher": teacher_to
                }
            })
        except Exception as e:
            print(f"⚠️ Ошибка при обработке строки: {e}")
            continue

    return schedule_data

def get_docx_schedule(group_name, page_url="http://www.bobruisk.belstu.by/dnevnoe-otdelenie/raspisanie-zanyatiy-i-zvonkov-zamenyi#gsc.tab=0"):
    docx_url = fetch_latest_docx_url(page_url)
    if not docx_url:
        return None

    if not has_docx_url_changed(docx_url):
        print("ℹ️ Ссылка на замену не изменилась — возможно, замены не обновились.")
    else:
        print("🔄 Обнаружена новая ссылка на замены.")

    try:
        doc = load_docx_from_url(docx_url)

        full_schedule = {
            "group": group_name,
            "schedule": []
        }

        for i, table in enumerate(doc.tables):
            label = weekday_map[(datetime.now().weekday() + i) % 7]
            result = parse_schedule_table(table, group_name, label)
            full_schedule["schedule"].extend(result["schedule"])

        if full_schedule["schedule"]:
            return full_schedule
        else:
            print(f"⚠️ Группа {group_name} не найдена в документе.")
            return full_schedule

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при скачивании файла: {e}")
        return None
    except Exception as e:
        print(f"❌ Ошибка при обработке DOCX: {e}")
        return None

def get_available_replacement_days(doc_schedule):
    days_with_replacements = set()

    for item in doc_schedule.get("schedule", []):
        if "to" in item and item.get("day"):
            days_with_replacements.add(item["day"].strip())

    return sorted(days_with_replacements)

if __name__ == '__main__':
    MY_GROUP = "РС02-24"
    schedule = get_docx_schedule(MY_GROUP)

    if schedule:
        print("✅ Получено расписание замен:")
        print(json.dumps(schedule, indent=4, ensure_ascii=False))

        available_days = get_available_replacement_days(schedule)
        print("\n📌 Дни, для которых найдены замены:")
        print(available_days)
