import json
import os
from datetime import datetime
import sys

COURSE_GROUPS = {
    "1": ["РС 02-25"],
    "2": ["РС 02-24"],
    "3": ["РС 02-23"],
    "4": ["ПО6"]
}

class GradeEntry:
    def __init__(self, student, subject, grade, grade_type, date):
        self.student = student
        self.subject = subject
        self.grade = grade
        self.grade_type = grade_type
        self.date = date

    def to_dict(self):
        return {
            "student": self.student,
            "subject": self.subject,
            "grade": self.grade,
            "grade_type": self.grade_type,
            "date": self.date
        }

    @staticmethod
    def from_dict(data):
        return GradeEntry(
            data["student"],
            data["subject"],
            data["grade"],
            data["grade_type"],
            data["date"]
        )

    def __str__(self):
        return f"{self.date} | {self.student} | {self.subject} | {self.grade} ({self.grade_type})"

class Journal:
    def __init__(self, filename):
        self.filename = filename
        self.entries = []
        self.students = []
        self.subjects = []
        self.load()

    def add_grade(self, student, subject, grade, grade_type, date):
        entry = GradeEntry(student, subject, grade, grade_type, date)
        self.entries.append(entry)
        self.save()
        print("Оценка добавлена.")

    def edit_grade(self, student, date, new_grade):
        for entry in self.entries:
            if entry.student == student and entry.date == date:
                entry.grade = new_grade
                self.save()
                print("Оценка изменена.")
                return
        print(" Оценка не найдена.")

    def show_grades(self):
        if not self.entries:
            print("Оценок нет.")
        else:
            for entry in self.entries:
                print(entry)

    def show_monthly_average(self, student):
        month = input("Введите месяц (мм): ").strip()
        year = input("Введите год (гггг): ").strip()
        filtered = [e for e in self.entries if e.student == student and e.date.endswith(f"{month}.{year}")]
        grades = [int(e.grade) for e in filtered if e.grade.isdigit()]
        if grades:
            avg = sum(grades) / len(grades)
            print(f" Средний балл за {month}.{year}: {avg:.2f}")
        else:
            print("Нет оценок за указанный месяц.")

    def add_student(self, name):
        if name not in self.students:
            self.students.append(name)
            self.save()
            print(f"Ученик '{name}' добавлен.")
        else:
            print("Такой ученик уже есть.")

    def delete_student_record(self, name):
        if name in self.students:
            self.students.remove(name)
            self.save()
            print(f"Ученик '{name}' удалён.")
        else:
            print("Такого ученика нет.")

    def add_subject(self, subject):
        if subject not in self.subjects:
            self.subjects.append(subject)
            self.save()
            print(f"Предмет '{subject}' добавлен.")
        else:
            print("Такой предмет уже есть.")

    def delete_subject_record(self, subject):
        if subject in self.subjects:
            self.subjects.remove(subject)
            self.save()
            print(f"Предмет '{subject}' удалён.")
        else:
            print("Такого предмета нет.")

    def save(self):
        data = {
            "entries": [e.to_dict() for e in self.entries],
            "students": self.students,
            "subjects": self.subjects
        }
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.entries = [GradeEntry.from_dict(e) for e in data.get("entries", [])]
                self.students = data.get("students", [])
                self.subjects = data.get("subjects", [])

class JournalSystem:
    def __init__(self):
        self.journals = {}
        for groups in COURSE_GROUPS.values():
            for group in groups:
                filename = f"{group.replace(' ', '_')}.json"
                self.journals[group] = Journal(filename)

    def select_group(self):
        print("\nВыберите курс:")
        for course_num in COURSE_GROUPS:
            print(f"{course_num}. Курс {course_num}")
        course = input("Введите номер курса: ").strip()
        if course not in COURSE_GROUPS:
            print("Неверный курс.")
            return None

        print("\nВыберите группу:")
        groups = COURSE_GROUPS[course]
        for i, group in enumerate(groups, 1):
            print(f"{i}. {group}")
        try:
            index = int(input("Введите номер группы: "))
            if 1 <= index <= len(groups):
                return groups[index - 1]
        except:
            print("Неверный ввод.")
        return None

    def get_journal(self, group_name):
        return self.journals.get(group_name)

def main():
    system = JournalSystem()
    
    group = system.select_group()
    if not group:
        print("Группа не выбрана. Выход.")
        return

    journal = system.get_journal(group)

    grade_type_map = {
        "1": "Обычная",
        "2": "ПР",
        "3": "ЛР",
        "4": "Не сдал"
    }

    while True:
        print(f"\nГруппа: {group}")
        print("Меню:")
        print("0. Сменить группу")
        print("1. Добавить оценку")
        print("2. Показать все оценки")
        print("3. Показать работы (ЛР и ПР)")
        print("4. Изменить оценку")
        print("5. Выход")
        print("6. Показать средний балл за месяц")
        print("7. Добавить ученика")
        print("8. Удалить ученика")
        print("9. Добавить предмет")
        print("10. Удалить предмет")

        choice = input("Выберите действие: ").strip()
        
        if choice == "0":
                print("Возврат к выбору группы.")
                break 

        if choice == "1":
            if not journal.students or not journal.subjects:
                print("Сначала добавьте учеников и предметы.")
                continue

            print("\nУченики:")
            for i, name in enumerate(journal.students, 1):
                print(f"{i}. {name}")
            try:
                student = journal.students[int(input("Выберите номер ученика: ")) - 1]
            except:
                print("Неверный ввод.")
                continue

            print("\nПредметы:")
            for i, subj in enumerate(journal.subjects, 1):
                print(f"{i}. {subj}")
            try:
                subject = journal.subjects[int(input("Выберите номер предмета: ")) - 1]
            except:
                print("Неверный ввод.")
                continue

            grade = input("Оценка: ").strip()
            print("\nТип оценки:")
            for k, v in grade_type_map.items():
                print(f"{k}. {v}")
            grade_type = grade_type_map.get(input("Выберите тип: ").strip())
            if not grade_type:
                print("Неверный тип.")
                continue

            date = input("Введите дату (дд.мм.гггг): ").strip()
            try:
                datetime.strptime(date, "%d.%m.%Y")
            except:
                print("Неверный формат даты.")
                continue

            journal.add_grade(student, subject, grade, grade_type, date)

        elif choice == "2":
            journal.show_grades()

        elif choice == "3":
            print("\nРаботы (ЛР и ПР):")
            for entry in journal.entries:
                if entry.grade_type in ["ЛР", "ПР"]:
                    print(entry)

        elif choice == "4":
            print("\nУченики:")
            for i, name in enumerate(journal.students, 1):
                print(f"{i}. {name}")
            try:
                student = journal.students[int(input("Выберите номер ученика: ")) - 1]
            except:
                print("Неверный ввод.")
                continue
            date = input("Введите дату оценки (дд.мм.гггг): ").strip()
            new_grade = input("Введите новую оценку: ").strip()
            journal.edit_grade(student, date, new_grade)

        elif choice == "5":
            print("Выход из программы.")
            sys.exit()

        elif choice == "6":
            if not journal.students:
                print("Список учеников пуст.")
                continue
            print("\nУченики:")
            for i, name in enumerate(journal.students, 1):
                print(f"{i}. {name}")
            try:
                student = journal.students[int(input("Выберите номер ученика: ")) - 1]
                journal.show_monthly_average(student)
            except:
                print("Неверный ввод.")

        elif choice == "7":
            name = input("Введите имя ученика: ").strip()
            journal.add_student(name)

        elif choice == "8":
            if not journal.students:
                print("Список учеников пуст.")
                continue
            print("\nУченики:")
            for i, name in enumerate(journal.students, 1):
                print(f"{i}. {name}")
            try:
                index = int(input("Выберите номер ученика для удаления: "))
                journal.delete_student_record(journal.students[index - 1])
            except:
                print("Неверный ввод.")

        elif choice == "9":
            subject = input("Введите название предмета: ").strip()
            journal.add_subject(subject)

        elif choice == "10":
            if not journal.subjects:
                print("Список предметов пуст.")
                continue
            print("\nПредметы:")
            for i, subj in enumerate(journal.subjects, 1):
                print(f"{i}. {subj}")
            try:
                index = int(input("Выберите номер предмета для удаления: "))
                journal.delete_subject_record(journal.subjects[index - 1])
            except:
                print("Неверный ввод.")

        else:
            print("Неверный выбор.")

if __name__ == "__main__":
    while True:
        main()
    
