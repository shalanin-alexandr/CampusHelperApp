import json
import os

class GradeEntry:
    def __init__(self, student, subject, grade, grade_type, date):
        self.student = student
        self.subject = subject
        self.grade = grade
        self.grade_type = grade_type
        self.date = date

    def __str__(self):
        return f"{self.date} | {self.student} | {self.subject} | {self.grade} ({self.grade_type})"

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

class Journal:
    def __init__(self):
        self.entries = []
        self.filename = "journal.json"
        self.load()

    def add_grade(self, student, subject, grade, grade_type, date):
        entry = GradeEntry(student, subject, grade, grade_type, date)
        self.entries.append(entry)
        self.save()
        print("Оценка добавлена.")

    def show_grades(self, student=None, subject=None, grade_type=None):
        print("\nЖурнал оценок:")
        for entry in self.entries:
            if (student is None or entry.student == student) and \
               (subject is None or entry.subject == subject) and \
               (grade_type is None or entry.grade_type == grade_type):
                print(entry)

    def edit_grade(self, student, date, new_grade):
        found = False
        for entry in self.entries:
            if entry.student == student and entry.date == date:
                print(f"Старое значение: {entry}")
                entry.grade = new_grade
                self.save()
                print(f"Оценка обновлена: {entry}")
                found = True
        if not found:
            print("Оценка не найдена. Проверь имя и дату.")

    def save(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump([entry.to_dict() for entry in self.entries], f, ensure_ascii=False, indent=4)

    def load(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.entries = [GradeEntry.from_dict(entry) for entry in data]

def main():
    journal = Journal()
    grade_type_map = {
        "1": "Обычная",
        "2": "ПР",
        "3": "ЛР",
        "4": "Не сдал"
    }

    while True:
        print("\nМеню:")
        print("1. Добавить оценку")
        print("2. Показать все оценки")
        print("3. Показать работы (ЛР и ПР)")
        print("4. Изменить оценку")
        print("5. Выход")

        choice = input("Выберите действие: ")

        if choice == "1":
            students = sorted(set(entry.student for entry in journal.entries))

            print("\nВы хотите:")
            print("1 - Выбрать ученика из списка")
            print("2 - Ввести нового ученика")
            student_choice = input("Введите номер: ")

            if student_choice == "1" and students:
                print("\nСуществующие ученики:")
                for i, name in enumerate(students, 1):
                    print(f"{i}. {name}")
                while True:
                    try:
                        index = int(input("Выберите номер ученика: "))
                        if 1 <= index <= len(students):
                            student = students[index - 1]
                            break
                        else:
                            print("Неверный номер. Попробуйте снова.")
                    except ValueError:
                        print("Введите число.")
            else:
                student = input("Введите имя нового ученика: ")

            subjects = sorted(set(entry.subject for entry in journal.entries))

            print("\nВы хотите:")
            print("1 - Выбрать предмет из списка")
            print("2 - Ввести новый предмет")
            subject_choice = input("Введите номер: ")

            if subject_choice == "1" and subjects:
                print("\nСуществующие предметы:")
                for i, subj in enumerate(subjects, 1):
                    print(f"{i}. {subj}")
                while True:
                    try:
                        index = int(input("Выберите номер предмета: "))
                        if 1 <= index <= len(subjects):
                            subject = subjects[index - 1]
                            break
                        else:
                            print("Неверный номер. Попробуйте снова.")
                    except ValueError:
                        print("Введите число.")
            else:
                subject = input("Введите название нового предмета: ")
            grade = input("Оценка: ")

            while True:
                print("\nВыберите тип оценки:")
                print("1 - Обычная")
                print("2 - ПР (Практическая работа)")
                print("3 - ЛР (Лабораторная работа)")
                print("4 - Не сдал")
                type_choice = input("Введите номер: ")
                if type_choice in grade_type_map:
                    grade_type = grade_type_map[type_choice]
                    break
                else:
                    print("Неверный выбор. Попробуйте снова.")

            date = input("Введите дату (в любом формате): ")
            journal.add_grade(student, subject, grade, grade_type, date)

        elif choice == "2":
            journal.show_grades()

        elif choice == "3":
            print("\nРаботы (ЛР и ПР):")
            for entry in journal.entries:
                if entry.grade_type in ["ЛР", "ПР"]:
                    print(entry)

        elif choice == "4":
            students = sorted(set(entry.student for entry in journal.entries))
            if not students:
                print("Нет оценок для редактирования.")
                continue

            print("\nУченики с оценками:")
            for i, name in enumerate(students, 1):
                print(f"{i}. {name}")

            while True:
                try:
                    index = int(input("Выберите номер ученика: "))
                    if 1 <= index <= len(students):
                        student = students[index - 1]
                        break
                    else:
                        print("Неверный номер. Попробуйте снова.")
                except ValueError:
                    print("Введите число.")

            date = input("Дата оценки (в любом формате): ")
            new_grade = input("Новая оценка: ")
            journal.edit_grade(student, date, new_grade)

        elif choice == "5":
            print("Выход из программы.")
            break

        else:
            print("Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main()
