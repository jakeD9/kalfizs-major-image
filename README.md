# Kalfiz Major Image

Local-first Raspberry Pi battlemap display and media manager for tabletop play. The project runs one backend-driven app that serves both a controller UI and a fullscreen kiosk display, with a later provisioning mode for WiFi setup on portable devices.

## What is implemented

- FastAPI app with:
  - `/control` controller UI for browsing media, uploads, folder creation, rename/delete, and display controls
  - `/display` fullscreen kiosk route
  - `/provision` WiFi provisioning page
  - health, status, media, display-state, websocket, and provisioning APIs
- Disk-backed media library rooted at `KALFIZ_MEDIA_ROOT` or `./media`
- In-memory display state with:
  - pending and active media
  - confirmation/apply flow
  - grid toggle, size, and offset
- Raspberry Pi helper scripts and `systemd` unit files for:
  - app startup
  - Chromium kiosk launch
  - boot mode selection
  - provisioning hotspot startup
- Pytest coverage for the core app flow

## Project layout

```text
docs/
  implementation.md
  plan.md
  roadmap.md
src/kalfiz_major_image/
  app.py
  config.py
  media.py
  display_state.py
  static/
  templates/
scripts/
systemd/
tests/
media/
```

Planning docs live in [docs/implementation.md](/Users/duckworth/projects/kalfizs-major-image/docs/implementation.md:1), [docs/roadmap.md](/Users/duckworth/projects/kalfizs-major-image/docs/roadmap.md:1), and [docs/plan.md](/Users/duckworth/projects/kalfizs-major-image/docs/plan.md:1).

## Quick start

1. Create a virtual environment and install dependencies.

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

2. Start the app locally.

```bash
kalfiz-major-image
```

3. Open the routes:

- `http://127.0.0.1:8000/control`
- `http://127.0.0.1:8000/display`
- `http://127.0.0.1:8000/provision`

## Configuration

Environment variables are prefixed with `KALFIZ_`.

- `KALFIZ_APP_HOST`
- `KALFIZ_APP_PORT`
- `KALFIZ_MEDIA_ROOT`
- `KALFIZ_RUNTIME_MODE`
- `KALFIZ_KIOSK_URL`
- `KALFIZ_GRID_DEFAULT_SIZE`
- `KALFIZ_HOTSPOT_SSID`
- `KALFIZ_HOTSPOT_ADDRESS`
- `KALFIZ_ALLOW_NETWORK_MUTATIONS`

Example:

```bash
export KALFIZ_MEDIA_ROOT=/opt/kalfiz-major-image/media
export KALFIZ_RUNTIME_MODE=runtime
export KALFIZ_KIOSK_URL=http://127.0.0.1:8000/display
```

`KALFIZ_ALLOW_NETWORK_MUTATIONS` defaults to `false`. Leave it off in local development. On a real Pi, set it to `true` only when you want `/api/provision/wifi` to call `nmcli`.

## Running tests

```bash
pytest
```

If you want auto-reload while developing, you can still use:

```bash
uvicorn kalfiz_major_image.app:app --reload
```

## Raspberry Pi deployment notes

- Target OS: Raspberry Pi OS Bookworm
- Native deployment first: no Docker is required
- Copy the repo to `/opt/kalfiz-major-image`
- Install dependencies into `/opt/kalfiz-major-image/.venv`
- Copy `systemd/*.service` into `/etc/systemd/system/`
- Set defaults in `/etc/default/kalfiz-major-image`
- Enable the units you need with `systemctl enable`

Suggested enablement flow:

- `kalfiz-app.service`
- `kalfiz-kiosk.service`
- `kalfiz-boot.service`
- `kalfiz-provision-hotspot.service`
- `kalfiz-provision-kiosk.service`

## Current scope

Implemented now:

- static image support for `jpg`, `jpeg`, `png`, `webp`
- basic media CRUD plus folder creation
- real-time display sync over websocket
- grid overlay controls
- provisioning UI and Pi integration scripts

Explicitly deferred:

- gif and mp4 playback
- USB import
- advanced file organization like move/copy
- persisted display state across restarts
- dev containers
