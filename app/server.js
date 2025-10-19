import express from 'express';
import cors from 'cors';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(cors());
app.use(express.json());

// 📂 Раздаём папку HTML как статику по виртуальному пути /html-static
app.use('/html-static', express.static(path.join(__dirname, 'HTML'), {
  setHeaders: (res, filePath) => {
    if (filePath.endsWith('app.db')) {
      res.status(403).end('Access denied');
    }
  }
}));

// 📄 Главная страница — welcome.html
const welcomePath = path.join(__dirname, 'HTML', 'welcome.html');
app.get('/', (req, res) => {
  if (fs.existsSync(welcomePath)) {
    res.sendFile(welcomePath);
  } else {
    console.error('❌ welcome.html не найден по пути:', welcomePath);
    res.status(404).send('welcome.html не найден');
  }
});

// 📌 Подключаем SQLite
let db;
(async () => {
  db = await open({
    filename: path.join(__dirname, 'app.db'),
    driver: sqlite3.Database
  });

  await db.exec(`
    CREATE TABLE IF NOT EXISTS students (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      firstName TEXT,
      lastName TEXT,
      course TEXT,
      groupName TEXT
    )
  `);

  console.log('✅ SQLite подключена:', path.join(__dirname, 'app.db'));
})();

// 📝 Регистрация
app.post('/api/register', async (req, res) => {
  const { firstName, lastName, course, group } = req.body;
  if (!firstName || !lastName || !course || !group) {
    return res.status(400).json({ error: 'Не все поля заполнены' });
  }

  try {
    await db.run(
      'INSERT INTO students (firstName, lastName, course, groupName) VALUES (?, ?, ?, ?)',
      [firstName, lastName, course, group]
    );
    res.json({ status: 'ok' });
  } catch (err) {
    console.error('Ошибка при сохранении:', err);
    res.status(500).json({ error: 'Ошибка сервера' });
  }
});

// 📋 Проверка
app.get('/api/students', async (req, res) => {
  try {
    const students = await db.all('SELECT * FROM students');
    res.json(students);
  } catch (err) {
    res.status(500).json({ error: 'Ошибка БД' });
  }
});

// 🚀 Запуск
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`🚀 Сервер запущен на http://localhost:${PORT}`);
  console.log(`📄 Путь до welcome.html: ${welcomePath}`);
});
