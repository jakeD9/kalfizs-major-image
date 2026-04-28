#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo on the Raspberry Pi." >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR="${INSTALL_DIR:-/opt/kalfiz-major-image}"
ENV_TARGET="/etc/default/kalfiz-major-image"
HOSTNAME_VALUE="${1:-${KALFIZ_DEVICE_HOSTNAME:-kalfiz}}"
PI_USER="${SUDO_USER:-${USER:-pi}}"

echo "Installing Kalfiz Major Image into ${INSTALL_DIR}"

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y \
  avahi-daemon \
  chromium-browser \
  network-manager \
  python3-venv

mkdir -p "$(dirname "${INSTALL_DIR}")"
mkdir -p "${INSTALL_DIR}"
cp -a "${ROOT_DIR}/." "${INSTALL_DIR}/"

chmod +x "${INSTALL_DIR}"/scripts/*.sh
mkdir -p "${INSTALL_DIR}/media"

if [[ ! -f "${ENV_TARGET}" ]]; then
  install -D -m 0644 "${INSTALL_DIR}/config/kalfiz-major-image.env.sample" "${ENV_TARGET}"
else
  echo "Keeping existing ${ENV_TARGET}"
fi

sed -i "s/^KALFIZ_DEVICE_HOSTNAME=.*/KALFIZ_DEVICE_HOSTNAME=${HOSTNAME_VALUE}/" "${ENV_TARGET}" || true
sed -i "s|^KALFIZ_MEDIA_ROOT=.*|KALFIZ_MEDIA_ROOT=${INSTALL_DIR}/media|" "${ENV_TARGET}" || true

python3 -m venv "${INSTALL_DIR}/.venv"
source "${INSTALL_DIR}/.venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install -e "${INSTALL_DIR}"

for service_file in "${INSTALL_DIR}"/systemd/*.service; do
  install -m 0644 "${service_file}" /etc/systemd/system/
done

"${INSTALL_DIR}/scripts/setup_mdns.sh" "${HOSTNAME_VALUE}"

systemctl daemon-reload
systemctl enable NetworkManager avahi-daemon kalfiz-boot.service
systemctl restart NetworkManager
systemctl restart avahi-daemon

if id -u "${PI_USER}" >/dev/null 2>&1; then
  chown -R "${PI_USER}:${PI_USER}" "${INSTALL_DIR}"
fi

echo
echo "Install complete."
echo "Edit ${ENV_TARGET} if you want to change ports, hotspot credentials, or hostname."
echo "Reboot the Pi, then open http://${HOSTNAME_VALUE}.local:8000/control from another device on the same WiFi."
