#!/bin/bash
# TV Time Rescue - launcher for Linux (run from source).
# Make it runnable once:  chmod +x START-HERE-Linux.sh
# Then run it:            ./START-HERE-Linux.sh

cd "$(dirname "$0")/.." || exit 1

echo "=================================================================="
echo "  TV Time Rescue"
echo "=================================================================="
echo

if command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  echo "Python 3 was not found. Install it with your package manager, for example:"
  echo "  sudo apt install python3 python3-pip"
  exit 1
fi

echo "Making sure the requirements are installed (quick after the first time)..."
"$PY" -m pip install --quiet --disable-pip-version-check -r requirements.txt 2>/dev/null || \
  echo "  (could not auto-install; unencrypted backups still work with no extra packages)"

echo
"$PY" run.py
