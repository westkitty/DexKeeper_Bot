# Linux build (unsigned)

This produces an unsigned AppImage.

Requirements on Linux:
- Python 3.11+
- curl (to download appimagetool)

Build steps:
1. Open a terminal in the repo root.
2. Run:
   `packaging/linux/build.sh`

Outputs:
- AppImage: `dist/linux/DexKeeper.AppImage`

Notes:
- The first time the app runs, it shows a GUI prompt for `BOT_TOKEN` and optional `ADMIN_ID`.
- Configuration and logs are stored in `~/.local/share/DexKeeper` (or `$XDG_DATA_HOME/DexKeeper`).
