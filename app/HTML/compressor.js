const fileInput = document.getElementById("file");
const fileBtn = document.getElementById("file-btn");
const sendBtn = document.getElementById("send-btn");
const textArea = document.getElementById("text");
const output = document.getElementById("output");

// приветственное сообщение
const assistantMsg = document.createElement("div");
assistantMsg.className = "assistant-message";
assistantMsg.textContent = "Загрузи файл или вставь текст — я перескажу тебе самое главное ✨";
output.appendChild(assistantMsg);

// кнопка выбора файла
fileBtn.onclick = () => fileInput.click();

// автообработка при выборе файла
fileInput.addEventListener("change", async () => {
  if (fileInput.files.length === 0) return;
  const file = fileInput.files[0];

  const userMsg = document.createElement("div");
  userMsg.className = "user-msg";
  userMsg.textContent = "📁 Загружен файл: " + file.name;
  output.appendChild(userMsg);
  output.scrollTop = output.scrollHeight;

  await sendToServer(file);
});

// текстовая отправка
sendBtn.addEventListener("click", async () => {
  const text = textArea.value.trim();
  if (!text) return;
  const userMsg = document.createElement("div");
  userMsg.className = "user-msg";
  userMsg.textContent = text;
  output.appendChild(userMsg);
  output.scrollTop = output.scrollHeight;

  textArea.value = "";
  sendBtn.classList.remove("active");

  await sendToServer(null, text);
});

// активация кнопки при вводе текста
textArea.addEventListener("input", () => {
  sendBtn.classList.toggle("active", textArea.value.trim().length > 0);
});

async function sendToServer(file = null, text = "") {
  const botMsg = document.createElement("div");
  botMsg.className = "bot-msg";
  output.appendChild(botMsg);
  output.scrollTop = output.scrollHeight;

  const formData = new FormData();
  formData.append("filename", "summary");
  if (file) formData.append("file", file);
  if (text) formData.append("text", text);

  try {
    const res = await fetch("/api/compress", { method: "POST", body: formData });
    const data = await res.json();

    if (data.summary) {
      botMsg.textContent = "";

      // эффект "печати"
      for (const line of data.summary) {
        for (let i = 0; i < line.length; i++) {
          botMsg.textContent += line[i];
          await new Promise(r => setTimeout(r, 12));
          output.scrollTop = output.scrollHeight;
        }
        botMsg.innerHTML += "<br><br>";
      }

      // кнопка "Сохранить"
      if (data.file) {
        const saveBtn = document.createElement("button");
        saveBtn.textContent = "💾 Сохранить DOCX";
        saveBtn.style.cssText = `
          margin-top: 8px;
          background: #2e82ff;
          border: none;
          color: white;
          padding: 8px 14px;
          border-radius: 8px;
          cursor: pointer;
          font-size: 14px;
        `;
        saveBtn.onclick = () => {
          window.location.href = "/api/download/" + data.file.split("/").pop();
        };
        botMsg.appendChild(saveBtn);
      }
    } else {
      botMsg.textContent = "❌ Ошибка при обработке.";
    }
  } catch (e) {
    botMsg.textContent = "⚠️ Не удалось подключиться к серверу.";
  }

  fileInput.value = "";
}
