#!/usr/bin/env bash
set -euo pipefail

if nmcli -t -f STATE general | grep -q '^connected'; then
  export KALFIZ_RUNTIME_MODE=runtime
  exec systemctl start kalfiz-app.service kalfiz-kiosk.service
fi

export KALFIZ_RUNTIME_MODE=provision
exec systemctl start kalfiz-app.service kalfiz-provision-kiosk.service
