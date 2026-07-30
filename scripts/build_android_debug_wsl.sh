#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
VENV_DIR="$HOME/.venvs/profeia-buildozer"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install "buildozer==1.5.0" "cython<3.0" virtualenv

cd "$FRONTEND_DIR"
"$VENV_DIR/bin/buildozer" -v android debug

echo ""
echo "APK generado en:"
echo "$FRONTEND_DIR/bin"
