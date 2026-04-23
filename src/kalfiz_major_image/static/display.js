const image = document.getElementById("display-image");
const grid = document.getElementById("display-grid");
const emptyState = document.getElementById("display-empty");

function renderDisplay(state) {
  const activePath = state.active_media_path;
  if (!activePath || !state.applied) {
    image.classList.add("hidden");
    grid.classList.add("hidden");
    emptyState.classList.remove("hidden");
    return;
  }

  image.src = `/media/${encodeURI(activePath)}?t=${encodeURIComponent(state.updated_at || Date.now())}`;
  image.classList.remove("hidden");
  emptyState.classList.add("hidden");

  if (state.grid.enabled) {
    grid.classList.remove("hidden");
    grid.style.backgroundSize = `${state.grid.size}px ${state.grid.size}px`;
    grid.style.backgroundPosition = `${state.grid.offset_x}px ${state.grid.offset_y}px`;
  } else {
    grid.classList.add("hidden");
  }
}

async function connect() {
  const initialResponse = await fetch("/api/display-state");
  renderDisplay(await initialResponse.json());

  const socketProtocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${socketProtocol}://${window.location.host}/ws/display`);
  socket.addEventListener("message", (event) => {
    renderDisplay(JSON.parse(event.data));
  });
  socket.addEventListener("close", () => {
    window.setTimeout(connect, 1000);
  });
}

connect();
