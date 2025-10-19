const startBtn = document.getElementById('startBtn');
const pauseBtn = document.getElementById('pauseBtn');
const resetBtn = document.getElementById('resetBtn');
const timeEl = document.getElementById('time');
const progressEl = document.getElementById('progress');
const sessionLabel = document.getElementById('session-label');
const bell = document.getElementById('bell');

const workMinInput = document.getElementById('workMin');
const shortMinInput = document.getElementById('shortMin');
const longMinInput = document.getElementById('longMin');
const cyclesInput = document.getElementById('cycles');

const modeBtns = document.querySelectorAll('.mode-btn');

let timer = null;
let remaining = 25 * 60;
let total = 25 * 60;
let state = 'stopped';
let mode = 'work';
let sessionCount = 0;

function formatTime(sec) {
  const m = Math.floor(sec / 60).toString().padStart(2, '0');
  const s = (sec % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

function setMode(newMode) {
  mode = newMode;
  modeBtns.forEach(b => b.classList.toggle('active', b.dataset.mode === newMode));
  let mins = getMinutesForMode();
  total = remaining = mins * 60;
  timeEl.textContent = formatTime(remaining);
  sessionLabel.textContent =
    mode === 'work' ? `Сессия ${sessionCount + 1}` :
    mode === 'short' ? 'Короткий перерыв' :
    'Длинный перерыв';
  updateProgress();
}

function getMinutesForMode() {
  const w = parseInt(workMinInput.value) || 25;
  const s = parseInt(shortMinInput.value) || 5;
  const l = parseInt(longMinInput.value) || 15;
  if (mode === 'work') return w;
  if (mode === 'short') return s;
  return l;
}

modeBtns.forEach(b => {
  b.addEventListener('click', () => {
    stopTimer();
    setMode(b.dataset.mode);
  });
});

function updateProgress() {
  const pct = total ? ((total - remaining) / total) * 360 : 0;
  progressEl.style.background = `conic-gradient(var(--accent) ${pct}deg, #1f1f1f ${pct}deg)`;
}

function tick() {
  if (remaining <= 0) {
    bell.currentTime = 0;
    bell.play().catch(() => {});
    if (mode === 'work') {
      sessionCount += 1;
      const cycles = parseInt(cyclesInput.value) || 4;
      if (sessionCount % cycles === 0) setMode('long');
      else setMode('short');
    } else {
      setMode('work');
    }
    startTimer();
    return;
  }
  remaining -= 1;
  timeEl.textContent = formatTime(remaining);
  updateProgress();
}

function startTimer() {
  if (state === 'running') return;
  state = 'running';
  startBtn.style.display = 'none';
  pauseBtn.style.display = 'inline-block';
  timer = setInterval(tick, 1000);
}

function stopTimer() {
  if (timer) clearInterval(timer);
  timer = null;
  state = 'stopped';
  startBtn.style.display = 'inline-block';
  pauseBtn.style.display = 'none';
}

function pauseTimer() {
  if (timer) clearInterval(timer);
  timer = null;
  state = 'paused';
  startBtn.style.display = 'inline-block';
  pauseBtn.style.display = 'none';
}

startBtn.addEventListener('click', () => {
  total = remaining = getMinutesForMode() * 60;
  startTimer();
});

pauseBtn.addEventListener('click', pauseTimer);

resetBtn.addEventListener('click', () => {
  stopTimer();
  sessionCount = 0;
  setMode('work');
});

[workMinInput, shortMinInput, longMinInput, cyclesInput].forEach(i => {
  i.addEventListener('change', () => {
    if (state !== 'running') {
      total = remaining = getMinutesForMode() * 60;
      timeEl.textContent = formatTime(remaining);
      updateProgress();
    }
  });
});

/* — исправление: функция теперь глобальна — */
window.changeValue = function(id, delta) {
  const el = document.getElementById(id);
  let val = parseInt(el.value) || 0;
  val = Math.min(Math.max(val + delta, parseInt(el.min) || 0), parseInt(el.max) || 999);
  el.value = val;
  el.dispatchEvent(new Event('change'));
};

if ('Notification' in window && Notification.permission === 'default') {
  try {
    Notification.requestPermission();
  } catch (e) {}
}

setMode('work');
