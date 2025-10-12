const gradeButtons = document.getElementById("grade-buttons");
const gradesList = document.getElementById("grades-list");
const averageValue = document.getElementById("average-value");
const averageArrow = document.getElementById("average-arrow");
const deleteLastBtn = document.getElementById("delete-last-btn");
const clearBtn = document.getElementById("clear-btn");
const gradesCount = document.getElementById("grades-count");

const gradeColors = {
  1: "#ef4444",
  2: "#f97316",
  3: "#f59e0b",
  4: "#eab308",
  5: "#84cc16",
  6: "#22c55e",
  7: "#10b981",
  8: "#14b8a6",
  9: "#06b6d4",
  10: "#3b82f6"
};

let grades = [];

function updateAverage() {
  if (grades.length === 0) {
    averageValue.textContent = "0.0";
    averageArrow.textContent = "0";
    averageArrow.style.backgroundColor = "#333";
    averageArrow.style.color = "#fff";
    return;
  }
  const sum = grades.reduce((a, b) => a + b, 0);
  const avg = sum / grades.length;
  const roundedAvg = Math.round(avg);
  averageValue.textContent = avg.toFixed(1);
  averageArrow.textContent = roundedAvg;
  averageArrow.style.backgroundColor = gradeColors[roundedAvg] || "#333";
  averageArrow.style.color = "#fff";
}

function updateGradesCount() {
  gradesCount.textContent = grades.length;
}

function renderGrades() {
  gradesList.innerHTML = "";
  if (grades.length === 0) {
    const emptyState = document.createElement("div");
    emptyState.className = "empty-state";
    emptyState.textContent = "Оценок пока нет";
    gradesList.appendChild(emptyState);
    return;
  }
  [...grades].reverse().forEach((grade, index) => {
    const tag = document.createElement("div");
    tag.className = "grade-tag";
    tag.textContent = grade;
    tag.style.backgroundColor = gradeColors[grade] || "#444";
    tag.title = `Оценка ${grade}`;
    tag.style.opacity = "0";
    tag.style.transform = "scale(0.9)";
    requestAnimationFrame(() => {
      tag.style.transition = "transform 220ms ease, opacity 220ms ease";
      tag.style.opacity = "1";
      tag.style.transform = "scale(1)";
    });
    gradesList.appendChild(tag);
  });
  gradesList.parentElement.scrollLeft = 0;
}

function addGrade(grade) {
  grades.push(grade);
  updateAverage();
  updateGradesCount();
  renderGrades();
}

// create buttons 1..10 inside grid
for (let i = 1; i <= 10; i++) {
  const btn = document.createElement("button");
  btn.className = "grade-btn";
  btn.type = "button";
  btn.textContent = i;
  btn.setAttribute("aria-label", `Оценка ${i}`);
  btn.style.borderColor = gradeColors[i];
  btn.addEventListener("click", () => {
    btn.animate([{ transform: "translateY(0)" }, { transform: "translateY(-4px)" }, { transform: "translateY(0)" }], { duration: 160 });
    addGrade(i);
  });
  gradeButtons.appendChild(btn);
}

// actions
deleteLastBtn.addEventListener("click", () => {
  if (grades.length > 0) {
    grades.pop();
    updateAverage();
    updateGradesCount();
    renderGrades();
  }
});

clearBtn.addEventListener("click", () => {
  if (grades.length > 0) {
    if (confirm("Удалить все оценки?")) {
      grades = [];
      updateAverage();
      updateGradesCount();
      renderGrades();
    }
  }
});

document.addEventListener('DOMContentLoaded', () => {
  updateAverage();
  updateGradesCount();
  renderGrades();
});

// Optional: if window tallness changes, ensure buttons grid reflows to fit
window.addEventListener('resize', () => {
  // keep grades list scrolled to start and ensure layout recalculation
  if (grades.length > 0) gradesList.parentElement.scrollLeft = 0;
});
