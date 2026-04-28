#!/usr/bin/env bash
set -euo pipefail

mkdir -p /run/kalfiz-major-image

if nmcli -t -f STATE general | grep -q '^connected'; then
  cat > /run/kalfiz-major-image/runtime.env <<'EOF'
KALFIZ_RUNTIME_MODE=runtime
EOF
  systemctl stop kalfiz-provision-hotspot.service kalfiz-provision-kiosk.service || true
  exec systemctl start kalfiz-app.service kalfiz-kiosk.service
fi

cat > /run/kalfiz-major-image/runtime.env <<'EOF'
KALFIZ_RUNTIME_MODE=provision
EOF
exec systemctl start kalfiz-provision-hotspot.service kalfiz-app.service kalfiz-provision-kiosk.service
