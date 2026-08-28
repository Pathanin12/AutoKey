#!/bin/bash
# Bump version, commit if needed, then push — ใช้แทน git push ทุกครั้ง
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ $# -lt 1 ]]; then
  echo "ใช้: ./scripts/push.sh <git push args...>"
  echo "ตัวอย่าง: ./scripts/push.sh origin main"
  exit 1
fi

PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  PYTHON=python
fi

NEW_VERSION="$("$PYTHON" scripts/bump_version.py)"
git add constants/version.py packaging/version_info.txt

if ! git diff --cached --quiet; then
  git commit -m "Bump version to ${NEW_VERSION}."
  echo "AutoKey v${NEW_VERSION} — version commit created"
fi

git push "$@"
