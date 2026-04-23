#!/usr/bin/env bash
set -euo pipefail

PROVISION_URL="${KALFIZ_PROVISION_URL:-http://127.0.0.1:8000/provision}"
CHROMIUM_BIN="${CHROMIUM_BIN:-chromium-browser}"

exec "${CHROMIUM_BIN}" \
  --kiosk \
  --incognito \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --noerrdialogs \
  "${PROVISION_URL}"
