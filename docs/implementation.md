# Kalfiz Major Image Implementation Plan

## Summary

Build this as a native Raspberry Pi OS application in phases, starting with the core local runtime on an already-connected Pi and deferring WiFi provisioning until the main controller/display workflow is stable. The initial architecture uses one backend-driven app with two UI surfaces: a controller route for managing images and selecting what to show, and a fullscreen display route for the kiosk monitor. Initial media scope is static images only (`jpg`, `png`, `webp`), with ephemeral display state and basic image-library CRUD.

## Phase 1: Core Runtime Skeleton and Display Proof

- Target Raspberry Pi OS Bookworm on Pi 4 with native `systemd` services and shell scripts, not Docker.
- Create one Python app that exposes:
  - a controller-facing route
  - a fullscreen display route for the kiosk screen
  - minimal health and status endpoints
- Define a single in-memory display state model:
  - selected image id/path
  - display confirmation status
  - grid enabled flag
  - grid settings for size and offset
- Start with a seeded local media directory and a manual image selection flow before uploads exist.
- Launch Chromium in kiosk mode against the display route on boot when the device is already connected to WiFi.

Independent test goal:
- On a Pi that already has network access, the app boots, Chromium opens fullscreen, and changing the selected test image updates the display route correctly.

## Phase 2: Local Media Library and Basic File Operations

- Add disk-backed media library support rooted in one configured storage directory on the Pi.
- Support only:
  - list media
  - preview media
  - upload media
  - rename media
  - delete media
  - create folders
- Explicitly defer:
  - move/copy workflows
  - USB import
  - GIF and MP4 playback
  - advanced reorganization tools
- Validate file type and filename safety at the API boundary.
- Reflect the on-disk folder structure in the controller UI rather than inventing a separate catalog/database.

Public interfaces to add:
- media listing endpoint
- upload endpoint
- rename endpoint
- delete endpoint
- preview and asset-serving endpoint

Independent test goal:
- A user on the same network can upload a valid image, see it appear in the library, rename it, delete it, and browse folders without breaking the on-disk structure.

## Phase 3: Real-Time Controller and Grid Overlay

- Add a controller UI for selecting an image, previewing it, and confirming display changes.
- Add real-time display synchronization using a websocket or equivalent push channel from the backend to the display route.
- Add a grid overlay on the display route with initial controls for:
  - toggle on/off
  - cell size
  - x/y offset
- Keep display state ephemeral in this phase; restarting the app resets the active display and grid state.

Public interfaces to add:
- display state read/update endpoint or websocket messages
- grid configuration payload in the display state contract

Independent test goal:
- From a laptop or phone on the same WiFi, the controller can select an uploaded image, confirm it, and the kiosk display updates live with grid changes without refreshing Chromium manually.

## Phase 4: Pi Startup Hardening and Operational Packaging

- Add production boot wiring:
  - app service startup
  - kiosk launch service
  - service ordering and restart behavior
- Add a simple configuration model for:
  - media root path
  - app port
  - display URL
  - kiosk/autostart flags
- Add install/setup scripts and concise docs so a fresh clone can be deployed to a Pi with minimal manual steps.
- Add local non-Pi development instructions first; add dev container support only after the runtime commands and folder structure are stable.

Independent test goal:
- A freshly prepared Pi on a known WiFi network reboots into a working controller and display setup with no manual post-boot intervention.

## Phase 5: WiFi Provisioning Fallback Mode

- Add a boot-time connectivity check that chooses between:
  - normal runtime mode when WiFi is available
  - provisioning mode when WiFi is unavailable
- In provisioning mode:
  - show clear setup instructions on the monitor
  - start a simple hotspot
  - host a lightweight setup page for entering WiFi credentials
  - save credentials through the OS/network stack
  - retry connection and switch into runtime mode after success
- Keep the provisioning UX intentionally simple rather than trying to emulate a polished captive portal.

Independent test goal:
- On a Pi without valid WiFi connectivity, the device presents setup instructions, accepts credentials through the setup page, joins the network, and then starts the normal app/kiosk flow.

## Public APIs and Interfaces

- Backend app serves both controller and display surfaces from one deployable service.
- Display state contract includes:
  - active media reference
  - confirmation/applied state
  - grid enabled
  - grid size
  - grid offset x/y
- Media API initially supports only static-image CRUD and folder creation.
- Runtime config should be file- or environment-based and avoid introducing a database in v1.
- Kiosk integration should be via native OS services and Chromium launch scripts.

## Test Plan

- Phase 1:
  - app starts on a Pi and on a local dev machine
  - display route renders a seeded image fullscreen
  - kiosk launch points at the correct route
- Phase 2:
  - valid image uploads succeed
  - invalid extensions are rejected
  - rename/delete operations update disk correctly
  - nested folder listing matches filesystem structure
- Phase 3:
  - controller selection updates the display in real time
  - confirmation gate prevents accidental display changes
  - grid toggle, size, and offset visibly affect the display as expected
- Phase 4:
  - reboot/startup tests confirm service ordering and restart recovery
  - fresh setup instructions produce a working device on known WiFi
- Phase 5:
  - no-WiFi boot enters provisioning mode
  - successful credential entry transitions into runtime mode
  - failed credential entry keeps the device recoverable and retryable

## Assumptions and Defaults

- OS target is Raspberry Pi OS Bookworm.
- Deployment is native first; Docker is out of scope for initial implementation.
- Frontend assumption is `Svelte` for the long-term controller/display UI, though the current implementation uses a lightweight server-rendered frontend to keep the runtime simple.
- Initial media support is `jpg`, `png`, and `webp` only.
- Initial file management is basic CRUD plus folder creation only.
- Current display state is ephemeral and not restored after restart.
- USB import, animated media, advanced organizer actions, and dev containers are explicitly deferred until after the core runtime is stable.
