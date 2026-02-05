#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$ROOT/assets/DexKeeper_Bot_icon.png"
ICONSET="$ROOT/assets/DexKeeper_Bot_icon.iconset"
ICNS="$ROOT/assets/DexKeeper_Bot_icon.icns"

mkdir -p "$ICONSET"

# Create a square 1024x1024 base (sips will resize, not crop)
BASE="$ROOT/assets/DexKeeper_Bot_icon_1024.png"
if [ ! -f "$BASE" ]; then
  sips -z 1024 1024 "$SRC" --out "$BASE" >/dev/null
fi

sips -z 16 16     "$BASE" --out "$ICONSET/icon_16x16.png" >/dev/null
sips -z 32 32     "$BASE" --out "$ICONSET/icon_16x16@2x.png" >/dev/null
sips -z 32 32     "$BASE" --out "$ICONSET/icon_32x32.png" >/dev/null
sips -z 64 64     "$BASE" --out "$ICONSET/icon_32x32@2x.png" >/dev/null
sips -z 128 128   "$BASE" --out "$ICONSET/icon_128x128.png" >/dev/null
sips -z 256 256   "$BASE" --out "$ICONSET/icon_128x128@2x.png" >/dev/null
sips -z 256 256   "$BASE" --out "$ICONSET/icon_256x256.png" >/dev/null
sips -z 512 512   "$BASE" --out "$ICONSET/icon_256x256@2x.png" >/dev/null
sips -z 512 512   "$BASE" --out "$ICONSET/icon_512x512.png" >/dev/null
sips -z 1024 1024 "$BASE" --out "$ICONSET/icon_512x512@2x.png" >/dev/null

iconutil -c icns "$ICONSET" -o "$ICNS"
rm -rf "$ICONSET"

echo "Wrote $ICNS"
