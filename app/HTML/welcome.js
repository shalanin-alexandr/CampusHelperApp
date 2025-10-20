// =====================
// 🌐 СЛАЙД-НАВИГАЦИЯ
// =====================
const slides = document.querySelectorAll('.slide');
const dots = document.querySelectorAll('.dot');
const dotsContainer = document.querySelector('.dots-container');
const bottomBtn = document.getElementById('bottom-btn');

let currentSlide = 0;

function goToSlide(index) {
  if (index < 0 || index >= slides.length) return;

  slides[currentSlide].classList.remove('active');
  slides[index].classList.add('active');
  currentSlide = index;

  updateDots();
  updateButton();
}

function updateDots() {
  dots.forEach((dot, i) => dot.classList.toggle('active', i === currentSlide));
  dotsContainer.style.display = currentSlide === slides.length - 1 ? 'none' : 'flex';
}

function updateButton() {
  if (currentSlide === slides.length - 1) {
    bottomBtn.style.display = 'none';
  } else if (currentSlide === slides.length - 2) {
    bottomBtn.textContent = 'Начать!';
  } else {
    bottomBtn.textContent = 'Далее';
    bottomBtn.style.display = 'block';
  }
}

bottomBtn.addEventListener('click', () => {
  goToSlide(currentSlide + 1);
});

// =====================
// 🧾 ГРУППЫ ПО КУРСАМ
// =====================
const groupsByCourse = {
  "1": ["ЛХ02-25","ТЭ13-25","РС02-25","ПМ04-25","ДП03-25"],
  "2": ["ЛХ02-24","ТЭ13-24","РС02-24","ПМ04-24","ЛХ02-25с"],
  "3": ["ЛХ02-23","ТЭ13-23","РС02-23","ПМ04-23","ДП03-24"],
  "4": ["ЛХ17","МД23","ПО6","ТМ3","ДП03-23"]
};

const courseSelect = document.getElementById('course');
const groupSelect = document.getElementById('group');

if (courseSelect) {
  courseSelect.addEventListener('change', () => {
    const course = courseSelect.value;
    groupSelect.innerHTML = '<option value="" disabled selected>Выбери группу</option>';
    groupsByCourse[course].forEach(gr => {
      const opt = document.createElement('option');
      opt.value = gr;
      opt.textContent = gr;
      groupSelect.appendChild(opt);
    });
  });
}

// =====================
// 📝 РЕГИСТРАЦИЯ
// =====================
const form = document.getElementById('register-form');
if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const data = {
      firstName: form.firstName.value.trim(),
      lastName: form.lastName.value.trim(),
      course: form.course.value,
      group: form.group.value
    };

    localStorage.setItem('student', JSON.stringify(data));

    try {
      await fetch('/api/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
      });
    } catch (err) {
      console.error('Ошибка регистрации:', err);
    }

    window.location.href = '/student';
  });
}

// =====================
// 🔸 ИНИЦИАЛИЗАЦИЯ
// =====================
window.addEventListener('DOMContentLoaded', () => {
  document.body.classList.add('loaded');
  updateDots();
  updateButton();
});
