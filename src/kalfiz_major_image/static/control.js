const state = {
  currentPath: "",
  selectedEntry: null,
  displayState: null,
};

const mediaList = document.getElementById("media-list");
const currentPath = document.getElementById("current-path");
const preview = document.getElementById("preview");
const message = document.getElementById("message");
const selectedPath = document.getElementById("selected-path");
const activePath = document.getElementById("active-path");

function setMessage(text, isError = false) {
  message.textContent = text;
  message.style.color = isError ? "#ff9e9e" : "";
}

function renderPreview(entry) {
  if (!entry || entry.kind !== "file") {
    preview.innerHTML = "<p>Select an image to preview it here before pushing to the kiosk display.</p>";
    return;
  }
  preview.innerHTML = `<img src="/media/${encodeURI(entry.relative_path)}" alt="${entry.name}" />`;
}

function renderEntries(entries) {
  mediaList.innerHTML = "";
  if (!entries.length) {
    mediaList.innerHTML = "<li class='media-item'><span>No files found in this folder yet.</span></li>";
    return;
  }
  entries.forEach((entry) => {
    const item = document.createElement("li");
    item.className = "media-item";
    if (state.selectedEntry?.relative_path === entry.relative_path) {
      item.classList.add("selected");
    }
    item.innerHTML = `
      <div>
        <strong>${entry.name}</strong>
        <div class="message">${entry.kind === "folder" ? "Folder" : `${Math.round((entry.size || 0) / 1024)} KB`}</div>
      </div>
      <button type="button">${entry.kind === "folder" ? "Open" : "Select"}</button>
    `;
    item.querySelector("button").addEventListener("click", () => {
      if (entry.kind === "folder") {
        state.currentPath = entry.relative_path;
        loadEntries();
        return;
      }
      state.selectedEntry = entry;
      selectedPath.textContent = entry.relative_path;
      renderPreview(entry);
      loadEntries();
    });
    mediaList.appendChild(item);
  });
}

async function loadEntries() {
  currentPath.textContent = state.currentPath ? `/${state.currentPath}` : "/";
  const url = new URL("/api/media", window.location.origin);
  if (state.currentPath) {
    url.searchParams.set("path", state.currentPath);
  }
  const response = await fetch(url);
  const payload = await response.json();
  renderEntries(payload.entries);
}

async function loadDisplayState() {
  const response = await fetch("/api/display-state");
  state.displayState = await response.json();
  selectedPath.textContent = state.selectedEntry?.relative_path || state.displayState.pending_media_path || "None";
  activePath.textContent = state.displayState.active_media_path || "None";
  document.getElementById("grid-enabled").checked = state.displayState.grid.enabled;
  document.getElementById("grid-size").value = state.displayState.grid.size;
  document.getElementById("grid-offset-x").value = state.displayState.grid.offset_x;
  document.getElementById("grid-offset-y").value = state.displayState.grid.offset_y;
}

async function updateDisplayState(body) {
  const response = await fetch("/api/display-state", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const payload = await response.json();
    throw new Error(payload.detail || "Failed to update display state");
  }
  state.displayState = await response.json();
  activePath.textContent = state.displayState.active_media_path || "None";
}

async function applySelection() {
  if (!state.selectedEntry) {
    setMessage("Select an image before applying it to the display.", true);
    return;
  }
  const response = await fetch("/api/display-state/apply", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      active_media_path: state.selectedEntry.relative_path,
      applied: true,
    }),
  });
  state.displayState = await response.json();
  activePath.textContent = state.displayState.active_media_path || "None";
  setMessage(`Applied ${state.selectedEntry.name} to the display.`);
}

document.getElementById("refresh-media").addEventListener("click", () => loadEntries());
document.getElementById("path-up").addEventListener("click", () => {
  if (!state.currentPath) {
    return;
  }
  const parent = state.currentPath.split("/").slice(0, -1).join("/");
  state.currentPath = parent;
  loadEntries();
});

document.getElementById("queue-button").addEventListener("click", async () => {
  if (!state.selectedEntry) {
    setMessage("Select an image before queueing it.", true);
    return;
  }
  await updateDisplayState({
    pending_media_path: state.selectedEntry.relative_path,
    applied: false,
  });
  selectedPath.textContent = state.selectedEntry.relative_path;
  setMessage(`Queued ${state.selectedEntry.name}. Confirm it when you are ready.`);
});

document.getElementById("apply-button").addEventListener("click", () => applySelection());

document.getElementById("upload-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = document.getElementById("upload-input");
  const file = input.files[0];
  if (!file) {
    setMessage("Choose an image to upload first.", true);
    return;
  }
  const formData = new FormData();
  formData.append("parent_path", state.currentPath);
  formData.append("file", file);
  const response = await fetch("/api/media/upload", { method: "POST", body: formData });
  if (!response.ok) {
    const payload = await response.json();
    setMessage(payload.detail || "Upload failed.", true);
    return;
  }
  input.value = "";
  setMessage(`Uploaded ${file.name}.`);
  await loadEntries();
});

document.getElementById("folder-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const folderInput = document.getElementById("folder-name");
  const folderName = folderInput.value.trim();
  if (!folderName) {
    setMessage("Enter a folder name first.", true);
    return;
  }
  const response = await fetch("/api/media/folder", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ parent_path: state.currentPath, folder_name: folderName }),
  });
  if (!response.ok) {
    const payload = await response.json();
    setMessage(payload.detail || "Folder creation failed.", true);
    return;
  }
  folderInput.value = "";
  setMessage(`Created folder ${folderName}.`);
  await loadEntries();
});

document.getElementById("rename-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.selectedEntry) {
    setMessage("Select a file or folder before renaming it.", true);
    return;
  }
  const renameInput = document.getElementById("rename-input");
  const newName = renameInput.value.trim();
  if (!newName) {
    setMessage("Enter the new name first.", true);
    return;
  }
  const response = await fetch("/api/media/rename", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_path: state.selectedEntry.relative_path, new_name: newName }),
  });
  if (!response.ok) {
    const payload = await response.json();
    setMessage(payload.detail || "Rename failed.", true);
    return;
  }
  renameInput.value = "";
  state.selectedEntry = null;
  selectedPath.textContent = "None";
  renderPreview(null);
  setMessage(`Renamed item to ${newName}.`);
  await loadEntries();
});

document.getElementById("delete-button").addEventListener("click", async () => {
  if (!state.selectedEntry) {
    setMessage("Select a file or folder before deleting it.", true);
    return;
  }
  const confirmed = window.confirm(`Delete ${state.selectedEntry.name}?`);
  if (!confirmed) {
    return;
  }
  const response = await fetch("/api/media", {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_path: state.selectedEntry.relative_path }),
  });
  if (!response.ok && response.status !== 204) {
    const payload = await response.json();
    setMessage(payload.detail || "Delete failed.", true);
    return;
  }
  setMessage(`Deleted ${state.selectedEntry.name}.`);
  state.selectedEntry = null;
  selectedPath.textContent = "None";
  renderPreview(null);
  await loadEntries();
});

["grid-enabled", "grid-size", "grid-offset-x", "grid-offset-y"].forEach((id) => {
  document.getElementById(id).addEventListener("change", async () => {
    try {
      await updateDisplayState({
        grid: {
          enabled: document.getElementById("grid-enabled").checked,
          size: Number(document.getElementById("grid-size").value),
          offset_x: Number(document.getElementById("grid-offset-x").value),
          offset_y: Number(document.getElementById("grid-offset-y").value),
        },
      });
      setMessage("Updated grid settings.");
    } catch (error) {
      setMessage(error.message, true);
    }
  });
});

async function init() {
  await Promise.all([loadEntries(), loadDisplayState()]);
}

init().catch((error) => setMessage(error.message, true));
