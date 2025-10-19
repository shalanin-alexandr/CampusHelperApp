// Pomodoro Timer Script

const timerDisplay = document.getElementById("timer");
const startBtn = document.getElementById("start-btn");
const resetBtn = document.getElementById("reset-btn");
const workInput = document.getElementById("work-time");
const breakInput = document.getElementById("break-time");
const addWorkBtn = document.getElementById("add-work");
const subWorkBtn = document.getElementById("sub-work");
const addBreakBtn = document.getElementById("add-break");
const subBreakBtn = document.getElementById("sub-break");

let isRunning = false;
let isWork = true;
let timer;
let remainingTime = 0;

// антиспам блокировка кликов
let lastClick = 0;
const clickDelay = 150; // миллисекунд

function safeClick(callback) {
  const now = Date.now();
  if (now - lastClick > clickDelay) {
    lastClick = now;
    callback();
  }
}

// Форматирование времени в mm:ss
function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

// Обновление дисплея таймера
function updateDisplay() {
  timerDisplay.textContent = formatTime(remainingTime);
}

// Запуск и остановка таймера
function toggleTimer() {
  if (!isRunning) {
    if (remainingTime === 0) {
      remainingTime = (isWork ? workInput.value : breakInput.value) * 60;
    }
    startTimer();
  } else {
    stopTimer();
  }
}

function startTimer() {
  isRunning = true;
  startBtn.textContent = "Пауза";

  timer = setInterval(() => {
    if (remainingTime > 0) {
      remainingTime--;
      updateDisplay();
    } else {
      stopTimer();
      isWork = !isWork;
      remainingTime = (isWork ? workInput.value : breakInput.value) * 60;
      updateDisplay();
      alert(isWork ? "Время работать!" : "Отдыхай!");
      startTimer();
    }
  }, 1000);
}

function stopTimer() {
  clearInterval(timer);
  isRunning = false;
  startBtn.textContent = "Старт";
}

function resetTimer() {
  stopTimer();
  isWork = true;
  remainingTime = workInput.value * 60;
  updateDisplay();
}

// Изменение времени работы/отдыха
function changeValue(input, delta) {
  const newValue = Math.max(1, Number(input.value) + delta);
  input.value = newValue;
  if (!isRunning) {
    remainingTime = workInput.value * 60;
    updateDisplay();
  }
}

// Инициализация
document.addEventListener("DOMContentLoaded", () => {
  remainingTime = workInput.value * 60;
  updateDisplay();
});

// Слушатели событий
startBtn.addEventListener("click", toggleTimer);
resetBtn.addEventListener("click", resetTimer);

addWorkBtn.addEventListener("click", () =>
  safeClick(() => changeValue(workInput, 1))
);
subWorkBtn.addEventListener("click", () =>
  safeClick(() => changeValue(workInput, -1))
);
addBreakBtn.addEventListener("click", () =>
  safeClick(() => changeValue(breakInput, 1))
);
subBreakBtn.addEventListener("click", () =>
  safeClick(() => changeValue(breakInput, -1))
);
