#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Virtual environment not found at ${VENV_DIR}. Create it with 'uv venv' and install dependencies first." >&2
  exit 1
fi

source "${VENV_DIR}/bin/activate"
exec kalfiz-major-image
