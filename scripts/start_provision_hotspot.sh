#!/usr/bin/env bash
set -euo pipefail

HOTSPOT_SSID="${KALFIZ_HOTSPOT_SSID:-Kalfiz-Setup}"
PASSWORD="${KALFIZ_HOTSPOT_PASSWORD:-battlemap123}"

nmcli device wifi hotspot ifname wlan0 ssid "${HOTSPOT_SSID}" password "${PASSWORD}"
