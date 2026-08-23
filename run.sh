#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"
PYTHON="/opt/homebrew/bin/python3.13"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "ไม่พบ Homebrew Python — ติดตั้งด้วย: brew install python@3.13 python-tk@3.13"
  exit 1
fi

if ! "$PYTHON" -c "import tkinter" >/dev/null 2>&1; then
  echo "ไม่พบ tkinter — ติดตั้งด้วย: brew install python-tk@3.13"
  exit 1
fi

if [ ! -d ".venv" ] || [ ! -f ".venv/pyvenv.cfg" ] || ! grep -q "3.13" ".venv/pyvenv.cfg"; then
  rm -rf .venv
  "$PYTHON" -m venv .venv
fi

source .venv/bin/activate
python -m pip install -U pip -q
pip install -r requirements.txt -q
python main.py
