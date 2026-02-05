# Windows build (unsigned)

This produces an unsigned Windows installer and a portable exe.

Requirements on Windows:
- Python 3.11+
- Inno Setup (optional, for installer)

Build steps:
1. Open PowerShell in the repo root.
2. Run:
   `packaging\windows\build.ps1`

Outputs:
- Portable exe: `dist\windows\DexKeeper.exe`
- Installer (if Inno Setup is installed): `dist\windows\DexKeeper-Setup.exe`

Notes:
- The first time the app runs, it shows a GUI prompt for `BOT_TOKEN` and optional `ADMIN_ID`.
- Configuration and logs are stored in `%APPDATA%\DexKeeper`.
- The build script generates `assets\DexKeeper_Bot_icon.ico` from the repo PNG icon.
