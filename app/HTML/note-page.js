// note-page.js

document.addEventListener("DOMContentLoaded", () => {
  const viewScreen = document.getElementById("view-notes");
  const readScreen = document.getElementById("read-note");
  const editScreen = document.getElementById("edit-note");

  const createNoteBtn = document.getElementById("create-note-btn");
  const backBtn = document.getElementById("back-btn");
  const backFromReadBtn = document.getElementById("back-from-read-btn");
  const editFromReadBtn = document.getElementById("edit-from-read-btn");

  const noteForm = document.getElementById("note-form");
  const noteTitleInput = document.getElementById("note-title");
  const noteTextInput = document.getElementById("note-text");
  const iconToggleBtn = document.getElementById("icon-toggle-btn");
  const iconOptions = document.getElementById("icon-options");
  const noteIconInput = document.getElementById("note-icon");
  const deleteNoteBtn = document.getElementById("delete-note-btn");

  const notesList = document.getElementById("notes-list");
  const emptyMessage = document.getElementById("empty-message");

  let notes = [];
  let currentNoteId = null;

  // 🟡 API функции
  async function fetchNotes() {
    const res = await fetch("/api/notes");
    notes = await res.json();
    renderNotes();
  }

  async function createNote(title, text, icon) {
    await fetch("/api/notes/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, text, icon }),
    });
    await fetchNotes();
  }

  async function updateNote(id, title, text, icon) {
    await fetch(`/api/notes/update/${id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, text, icon }),
    });
    await fetchNotes();
  }

  async function deleteNote(id) {
    await fetch(`/api/notes/delete/${id}`, { method: "POST" });
    await fetchNotes();
  }

  // 📝 Рендер заметок
  function renderNotes() {
    notesList.innerHTML = "";
    if (notes.length === 0) {
      emptyMessage.style.display = "block";
    } else {
      emptyMessage.style.display = "none";
      notes.forEach(note => {
        const div = document.createElement("div");
        div.className = "note-tile";
        div.innerHTML = `
          <div class="note-icon">${note.icon || "📝"}</div>
          <div class="note-content">
            <h3>${note.title || "(Без названия)"}</h3>
            <p>${(note.text || "").substring(0, 80)}...</p>
          </div>
        `;
        div.addEventListener("click", () => openReadScreen(note));
        notesList.appendChild(div);
      });
    }
  }

  function openReadScreen(note) {
    document.getElementById("read-note-title").textContent = note.title || "(Без названия)";
    document.getElementById("read-note-text").textContent = note.text;
    document.getElementById("read-note-icon").textContent = note.icon || "📝";
    currentNoteId = note.id;
    switchScreen(readScreen);
  }

  function switchScreen(screen) {
    [viewScreen, readScreen, editScreen].forEach(s => s.classList.remove("visible"));
    screen.classList.add("visible");
  }

  createNoteBtn.addEventListener("click", () => {
    currentNoteId = null;
    noteTitleInput.value = "";
    noteTextInput.value = "";
    noteIconInput.value = "";
    deleteNoteBtn.style.display = "none";
    switchScreen(editScreen);
  });

  backBtn.addEventListener("click", () => switchScreen(viewScreen));
  backFromReadBtn.addEventListener("click", () => switchScreen(viewScreen));

  editFromReadBtn.addEventListener("click", () => {
    const note = notes.find(n => n.id === currentNoteId);
    if (note) {
      noteTitleInput.value = note.title;
      noteTextInput.value = note.text;
      noteIconInput.value = note.icon;
      deleteNoteBtn.style.display = "block";
      switchScreen(editScreen);
    }
  });

  iconToggleBtn.addEventListener("click", () => {
    iconOptions.classList.toggle("show");
  });

  iconOptions.querySelectorAll(".icon-choice").forEach(btn => {
    btn.addEventListener("click", () => {
      iconOptions.querySelectorAll(".icon-choice").forEach(b => b.classList.remove("selected"));
      btn.classList.add("selected");
      noteIconInput.value = btn.textContent;
    });
  });

  noteForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = noteTitleInput.value.trim();
    const text = noteTextInput.value.trim();
    const icon = noteIconInput.value || "📝";

    if (currentNoteId) {
      await updateNote(currentNoteId, title, text, icon);
    } else {
      await createNote(title, text, icon);
    }

    currentNoteId = null;
    switchScreen(viewScreen);
  });

  deleteNoteBtn.addEventListener("click", async () => {
    if (currentNoteId && confirm("Удалить эту заметку?")) {
      await deleteNote(currentNoteId);
      currentNoteId = null;
      switchScreen(viewScreen);
    }
  });

  fetchNotes();
});
