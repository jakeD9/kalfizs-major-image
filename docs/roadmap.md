# Kalfiz Major Image Roadmap

This roadmap is meant to track implementation progress in phases that can be built, tested, and validated independently.

## Status Legend

- `Not Started`
- `In Progress`
- `Blocked`
- `Done`

## Phase 1: Core Runtime Skeleton

Status: `Done`

Goal:
- Boot the app on an already-connected Pi and prove the controller-to-display loop.

Scope:
- Native Raspberry Pi OS target
- One backend app serving controller and fullscreen display routes
- Health and status endpoints
- In-memory display state
- Seeded local media directory
- Chromium kiosk startup script

Exit criteria:
- App starts locally and on Pi
- `/display` renders a selected image
- Kiosk launch targets the display route

## Phase 2: Local Media Library

Status: `Done`

Goal:
- Add disk-backed media management for static images.

Scope:
- Media listing
- Upload
- Rename
- Delete
- Folder creation
- Filesystem-safe path validation
- On-disk folder structure reflected in the UI

Exit criteria:
- Valid image uploads succeed
- Invalid file types are rejected
- Rename and delete work safely
- Folder browsing matches the filesystem structure

## Phase 3: Real-Time Display Controls

Status: `Done`

Goal:
- Make the display reactive to controller actions with a confirmation flow and grid controls.

Scope:
- Pending vs active display selection
- Confirm/apply workflow
- Websocket display updates
- Grid toggle
- Grid size and offset controls

Exit criteria:
- Controller updates appear on the display without a manual refresh
- Grid changes are reflected live
- Confirmation prevents accidental display changes

## Phase 4: Pi Startup Hardening

Status: `Done`

Goal:
- Make the app operable as a Pi appliance with native scripts and `systemd`.

Scope:
- App startup script
- Kiosk startup script
- Boot mode selection script
- `systemd` service files
- Configurable environment defaults
- Setup and deployment docs

Exit criteria:
- Fresh Pi setup can boot into the app on a known WiFi network
- Service ordering and restart behavior are defined
- Deployment steps are documented

## Phase 5: WiFi Provisioning Fallback

Status: `Partially Done`

Goal:
- Provide a fallback mode for devices that boot without WiFi connectivity.

Scope:
- Provisioning page and API
- Hotspot startup script
- Provisioning kiosk startup script
- Boot mode split between runtime and provisioning
- `nmcli`-based WiFi connection hook

Remaining work:
- Validate and harden the provisioning flow on real Pi hardware
- Wire service dependencies for hotspot startup in the intended boot sequence
- Confirm successful transition from provisioning mode back to runtime mode after a connection succeeds
- Add failure/retry UX details on the monitor and web UI

Exit criteria:
- No-WiFi boot enters provisioning mode
- User can submit WiFi credentials from the setup page
- Pi joins the target WiFi and transitions into runtime mode reliably

## Deferred Work

Status: `Not Started`

Items intentionally deferred from the current implementation:
- GIF support
- MP4/video playback
- USB media import
- Move/copy/reorganize workflows
- Persisted display state across restarts
- Dev container setup
- Svelte frontend replacement for the current lightweight server-rendered UI
