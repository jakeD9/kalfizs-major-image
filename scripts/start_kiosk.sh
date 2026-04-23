#!/usr/bin/env bash
set -euo pipefail

DISPLAY_URL="${KALFIZ_KIOSK_URL:-http://127.0.0.1:8000/display}"
CHROMIUM_BIN="${CHROMIUM_BIN:-chromium-browser}"

exec "${CHROMIUM_BIN}" \
  --kiosk \
  --incognito \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --noerrdialogs \
  "${DISPLAY_URL}"
