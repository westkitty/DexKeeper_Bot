#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV="$ROOT/.venv-linux-build"
PY="$VENV/bin/python"
PYINSTALLER="$VENV/bin/pyinstaller"

if [ ! -x "$PY" ]; then
  python3 -m venv "$VENV"
fi

"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r "$ROOT/requirements.txt"
"$PY" -m pip install pyinstaller

SPEC="$ROOT/packaging/linux/pyinstaller.spec"
DIST="$ROOT/dist/linux"
BUILD="$ROOT/build/linux"

"$PYINSTALLER" "$SPEC" --noconfirm --clean --distpath "$DIST" --workpath "$BUILD"

APPDIR="$DIST/DexKeeper.AppDir"
BIN_SRC=""
if [ -f "$DIST/DexKeeper" ]; then
  BIN_SRC="$DIST/DexKeeper"
elif [ -f "$DIST/DexKeeper/DexKeeper" ]; then
  BIN_SRC="$DIST/DexKeeper/DexKeeper"
else
  echo "DexKeeper binary not found in dist. Expected $DIST/DexKeeper or $DIST/DexKeeper/DexKeeper"
  exit 1
fi

mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

cp "$BIN_SRC" "$APPDIR/usr/bin/DexKeeper"
cp "$ROOT/packaging/linux/DexKeeper.desktop" "$APPDIR/usr/share/applications/DexKeeper.desktop"
cp "$ROOT/assets/DexKeeper_Bot_icon_256.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/DexKeeper.png"
cp "$ROOT/packaging/linux/AppRun" "$APPDIR/AppRun"
chmod +x "$APPDIR/AppRun"

# AppImage expects a .desktop file and icon at the AppDir root
cp "$ROOT/packaging/linux/DexKeeper.desktop" "$APPDIR/DexKeeper.desktop"
cp "$ROOT/assets/DexKeeper_Bot_icon_256.png" "$APPDIR/DexKeeper.png"

if [ ! -f "$APPDIR/DexKeeper.desktop" ]; then
  echo "Desktop file missing at $APPDIR/DexKeeper.desktop"
  ls -la "$APPDIR" || true
  exit 1
fi

APPIMAGETOOL="${APPIMAGETOOL:-}" 
if [ -z "$APPIMAGETOOL" ]; then
  APPIMAGETOOL="$ROOT/build/appimagetool.AppImage"
  if [ ! -f "$APPIMAGETOOL" ]; then
    set +e
    curl -L --fail "https://github.com/AppImage/AppImageKit/releases/latest/download/appimagetool-x86_64.AppImage" -o "$APPIMAGETOOL"
    if [ $? -ne 0 ] || [ ! -s "$APPIMAGETOOL" ]; then
      curl -L --fail "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -o "$APPIMAGETOOL"
    fi
    set -e
    chmod +x "$APPIMAGETOOL"
  fi
fi

if [ "$(head -c 4 "$APPIMAGETOOL" 2>/dev/null)" != $'\x7fELF' ]; then
  echo "appimagetool download is not a valid ELF binary."
  head -c 200 "$APPIMAGETOOL" || true
  exit 1
fi

APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL" "$APPDIR" "$DIST/DexKeeper.AppImage"

echo "AppImage created: $DIST/DexKeeper.AppImage"
