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
config/
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
- `KALFIZ_DEVICE_HOSTNAME`
- `KALFIZ_KIOSK_URL`
- `KALFIZ_PROVISION_URL`
- `KALFIZ_GRID_DEFAULT_SIZE`
- `KALFIZ_HOTSPOT_SSID`
- `KALFIZ_HOTSPOT_PASSWORD`
- `KALFIZ_HOTSPOT_ADDRESS`
- `KALFIZ_ALLOW_NETWORK_MUTATIONS`

Example:

```bash
export KALFIZ_MEDIA_ROOT=/opt/kalfiz-major-image/media
export KALFIZ_RUNTIME_MODE=runtime
export KALFIZ_DEVICE_HOSTNAME=kalfiz
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
- The simplest setup path is the installer script below

### One-command Pi install

From a fresh Raspberry Pi OS Bookworm device:

```bash
sudo apt-get update
sudo apt-get install -y git
git clone https://github.com/<your-account>/kalfiz-major-image.git
cd kalfiz-major-image
sudo ./scripts/install_pi.sh kalfiz
sudo reboot
```

What the installer does:

- installs required OS packages:
  - `python3-venv`
  - `chromium-browser`
  - `network-manager`
  - `avahi-daemon`
- copies the project into `/opt/kalfiz-major-image`
- creates `/etc/default/kalfiz-major-image` from [config/kalfiz-major-image.env.sample](/Users/duckworth/projects/kalfizs-major-image/config/kalfiz-major-image.env.sample:1) if needed
- creates a virtualenv and installs the app into it
- copies the `systemd` units into `/etc/systemd/system/`
- sets the Pi hostname and enables mDNS
- enables `NetworkManager`, `avahi-daemon`, and `kalfiz-boot.service`

After reboot, the controller UI should be reachable at `http://kalfiz.local:8000/control` by default.

### Manual Pi install

If you want to do it yourself instead of the installer:

```bash
sudo apt-get update
sudo apt-get install -y python3-venv chromium-browser network-manager avahi-daemon
sudo mkdir -p /opt/kalfiz-major-image
sudo cp -a . /opt/kalfiz-major-image
cd /opt/kalfiz-major-image
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
sudo install -D -m 0644 config/kalfiz-major-image.env.sample /etc/default/kalfiz-major-image
for service_file in systemd/*.service; do sudo install -m 0644 "$service_file" /etc/systemd/system/; done
sudo ./scripts/setup_mdns.sh kalfiz
sudo systemctl daemon-reload
sudo systemctl enable NetworkManager avahi-daemon kalfiz-boot.service
sudo reboot
```

Once connected to WiFi, the controller UI should be reachable from another device on the same network at `http://kalfiz.local:8000/control` by default. Change `KALFIZ_DEVICE_HOSTNAME` if you want a different `.local` name.

### Environment file on the Pi

The systemd units read environment variables from `/etc/default/kalfiz-major-image`. Use [config/kalfiz-major-image.env.sample](/Users/duckworth/projects/kalfizs-major-image/config/kalfiz-major-image.env.sample:1) as the template.

Important note:
- You generally only need to enable `kalfiz-boot.service`
- `kalfiz-boot.service` decides whether to start runtime mode or provisioning mode
- The app, kiosk, and hotspot services are started by that boot service as needed

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
