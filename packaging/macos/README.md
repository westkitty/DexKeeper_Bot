# macOS build (unsigned)

This produces an unsigned macOS .app and .dmg.

Requirements on macOS:
- Python 3.11+
- Xcode command line tools (for `iconutil`)

Build steps:
1. Open Terminal in the repo root.
2. Run:
   `packaging/macos/build.sh`

Outputs:
- App bundle: `dist/macos/DexKeeper.app`
- Disk image: `dist/macos/DexKeeper.dmg`

Notes:
- The first time the app runs, it shows a GUI prompt for `BOT_TOKEN` and optional `ADMIN_ID`.
- Configuration and logs are stored in `~/Library/Application Support/DexKeeper`.
