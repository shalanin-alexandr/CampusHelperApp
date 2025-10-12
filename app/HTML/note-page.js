document.addEventListener("DOMContentLoaded", () => {
  const viewNotes = document.getElementById("view-notes");
  const editNote = document.getElementById("edit-note");
  const readNote = document.getElementById("read-note");

  const notesList = document.getElementById("notes-list");
  const emptyMessage = document.getElementById("empty-message");

  const createBtn = document.getElementById("create-note-btn");
  const backBtn = document.getElementById("back-btn");
  const backFromReadBtn = document.getElementById("back-from-read-btn");
  const editFromReadBtn = document.getElementById("edit-from-read-btn");

  const noteForm = document.getElementById("note-form");
  const titleInput = document.getElementById("note-title");
  const textInput = document.getElementById("note-text");
  const iconInput = document.getElementById("note-icon");
  const editModeTitle = document.getElementById("edit-mode-title");

  const iconButtons = document.querySelectorAll(".icon-choice");
  const iconToggleBtn = document.getElementById("icon-toggle-btn");
  const iconOptions = document.getElementById("icon-options");

  const readNoteIcon = document.getElementById("read-note-icon");
  const readNoteTitle = document.getElementById("read-note-title");
  const readNoteText = document.getElementById("read-note-text");

  let notes = [];
  let editingIndex = null;

  function showScreen(screen) {
    viewNotes.classList.remove("visible");
    editNote.classList.remove("visible");
    readNote.classList.remove("visible");
    screen.classList.add("visible");
  }

  function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric"
    });
  }

  function renderNotes() {
    notesList.innerHTML = "";
    if (notes.length === 0) {
      emptyMessage.style.display = "block";
    } else {
      emptyMessage.style.display = "none";
      notes.forEach((note, index) => {
        const tile = document.createElement("div");
        tile.className = "note-tile";
        const previewText =
          note.text.length > 20 ? note.text.slice(0, 20) + "..." : note.text;

        tile.innerHTML = `
          <div class="note-meta">${formatDate(note.created)}</div>
          <div class="note-icon">${note.icon || "📝"}</div>
          <div class="note-content">
            <h3>${note.title}</h3>
            <p>${previewText}</p>
          </div>
        `;
        tile.addEventListener("click", () => showNote(index));
        notesList.appendChild(tile);
      });
    }
  }

  function showNote(index) {
    const note = notes[index];
    editingIndex = index;
    readNoteIcon.textContent = note.icon || "📝";
    readNoteTitle.textContent = note.title;
    readNoteText.textContent = note.text;
    showScreen(readNote);
  }

  function editNoteAt(index) {
    const note = notes[index];
    editingIndex = index;
    titleInput.value = note.title;
    textInput.value = note.text;
    iconInput.value = note.icon || "";
    editModeTitle.textContent = "Редактирование";
    selectIcon(note.icon || "");
    showScreen(editNote);
  }

  function clearIconSelection() {
    iconButtons.forEach(btn => btn.classList.remove("selected"));
  }

  function selectIcon(icon) {
    clearIconSelection();
    iconButtons.forEach(btn => {
      if (btn.textContent === icon) {
        btn.classList.add("selected");
      }
    });
    iconInput.value = icon;
  }

  iconButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      selectIcon(btn.textContent);
    });
  });

  iconToggleBtn.addEventListener("click", () => {
    iconOptions.classList.toggle("show");
  });

  createBtn.addEventListener("click", () => {
    editingIndex = null;
    titleInput.value = "";
    textInput.value = "";
    iconInput.value = "";
    editModeTitle.textContent = "Новая заметка";
    clearIconSelection();
    showScreen(editNote);
  });

  backBtn.addEventListener("click", () => {
    showScreen(viewNotes);
  });

  backFromReadBtn.addEventListener("click", () => {
    showScreen(viewNotes);
  });

  editFromReadBtn.addEventListener("click", () => {
    editNoteAt(editingIndex);
  });

  noteForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const selectedIcon = iconInput.value.trim() || "📝";

    const newNote = {
      title: titleInput.value.trim(),
      text: textInput.value.trim(),
      icon: selectedIcon,
      created: new Date().toISOString()
    };

    if (editingIndex !== null) {
      notes[editingIndex] = newNote;
    } else {
      notes.push(newNote);
    }

    renderNotes();
    showScreen(viewNotes);
  });

  renderNotes();
});
