#!/bin/bash
# TV Time Rescue - double-click launcher for macOS (run from source).
# If you downloaded the ready-made tvtime-rescue-macos you do NOT need this.
#
# First time only: right-click this file and choose Open (it is a script, so
# macOS asks for confirmation). If double-click does nothing, run once in
# Terminal:  chmod +x START-HERE-Mac.command

cd "$(dirname "$0")/.." || exit 1

echo "=================================================================="
echo "  TV Time Rescue"
echo "=================================================================="
echo

if command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  echo "Python 3 was not found."
  echo "Install it from https://www.python.org/downloads/macos/ and run this again."
  echo
  read -r -p "Press Enter to close..."
  exit 1
fi

echo "Making sure the requirements are installed (quick after the first time)..."
"$PY" -m pip install --quiet --disable-pip-version-check -r requirements.txt

echo
"$PY" run.py

echo
read -r -p "Press Enter to close..."
