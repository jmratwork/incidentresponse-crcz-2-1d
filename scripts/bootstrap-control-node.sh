#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "[ERROR] Python no encontrado: $PYTHON_BIN" >&2
  exit 1
fi

"$PYTHON_BIN" -m venv "$VENV_DIR"
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r "$ROOT_DIR/requirements.txt"
ansible-galaxy collection install -r "$ROOT_DIR/requirements.yml"

echo "[OK] Nodo de control preparado en $VENV_DIR"
echo "[INFO] Activa el entorno con: source $VENV_DIR/bin/activate"
