#!/usr/bin/env bash
set -euo pipefail

HOSTNAME_VALUE="${1:-${KALFIZ_DEVICE_HOSTNAME:-kalfiz}}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script as root so it can update the system hostname and enable avahi-daemon." >&2
  exit 1
fi

hostnamectl set-hostname "${HOSTNAME_VALUE}"
apt-get update
apt-get install -y avahi-daemon
systemctl enable avahi-daemon
systemctl restart avahi-daemon

echo "mDNS is configured. The Pi should now be reachable at http://${HOSTNAME_VALUE}.local:8000/control on the local network."
