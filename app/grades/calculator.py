class GradeTracker:
    def __init__(self):
        self.grades: list[int] = []

    def add_grade(self, value: int) -> None:
        if 1 <= value <= 10:
            self.grades.append(value)

    def remove_last(self) -> None:
        if self.grades:
            self.grades.pop()

    def get_average(self) -> float:
        if not self.grades:
            return 0.0
        return round(sum(self.grades) / len(self.grades), 2)

    def get_count(self) -> int:
        return len(self.grades)


if __name__ == '__main__':
    tracker = GradeTracker()
    tracker.add_grade(8)
    tracker.add_grade(9)
    tracker.add_grade(7)
    print(f"Средняя оценка: {tracker.get_average()}")
    print(f"Количество оценок: {tracker.get_count()}")
    tracker.remove_last()
    print(f"После удаления: {tracker.get_average()} ({tracker.get_count()} шт.)")
