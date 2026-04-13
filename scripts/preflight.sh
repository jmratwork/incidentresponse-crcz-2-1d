#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$ROOT_DIR/scripts/preflight.py"

if command -v ansible-playbook >/dev/null 2>&1; then
  ansible-playbook -i "$ROOT_DIR/inventory.example.ini" "$ROOT_DIR/provisioning/case-1d/provisioning/preflight.yml" --syntax-check
else
  echo "[WARN] ansible-playbook no está instalado; se omite syntax-check de preflight.yml"
fi
