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
"$PY" -m pip install pyobjc

"$ROOT/packaging/macos/make_icon.sh"

SPEC="$ROOT/packaging/macos/pyinstaller.spec"
DIST="$ROOT/dist/macos"
BUILD="$ROOT/build/macos"

"$PYINSTALLER" "$SPEC" --noconfirm --clean --distpath "$DIST" --workpath "$BUILD"

APP="$DIST/DexKeeper.app"
DMG="$DIST/DexKeeper.dmg"
ZIP="$DIST/DexKeeper-macos.zip"
if [ ! -d "$APP" ]; then
  echo "App bundle not found at $APP"
  exit 1
fi

if hdiutil create -volname "DexKeeper" -srcfolder "$APP" -ov -format UDZO "$DMG"; then
  echo "DMG created: $DMG"
else
  echo "DMG creation failed; falling back to zip"
fi

ditto -c -k --sequesterRsrc --keepParent "$APP" "$ZIP"
echo "Zip created: $ZIP"
