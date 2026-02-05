#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV="$ROOT/.venv-macos-build"
PY="$VENV/bin/python"
PYINSTALLER="$VENV/bin/pyinstaller"

if [ ! -x "$PY" ]; then
  python3 -m venv "$VENV"
fi

"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r "$ROOT/requirements.txt"
"$PY" -m pip install pyinstaller

"$ROOT/packaging/macos/make_icon.sh"

SPEC="$ROOT/packaging/macos/pyinstaller.spec"
DIST="$ROOT/dist/macos"
BUILD="$ROOT/build/macos"

"$PYINSTALLER" "$SPEC" --noconfirm --clean --distpath "$DIST" --workpath "$BUILD"

APP="$DIST/DexKeeper.app"
DMG="$DIST/DexKeeper.dmg"
if [ -d "$APP" ]; then
  hdiutil create -volname "DexKeeper" -srcfolder "$APP" -ov -format UDZO "$DMG"
  echo "DMG created: $DMG"
else
  echo "App bundle not found at $APP"
fi
