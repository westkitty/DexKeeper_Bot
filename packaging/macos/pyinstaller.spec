# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

root = Path(__file__).resolve().parents[2]
entry = root / "Sources" / "DexKeeper_Bot" / "dexkeeper_bot.py"
icon_path = root / "assets" / "DexKeeper_Bot_icon.icns"

block_cipher = None

a = Analysis(
    [str(entry)],
    pathex=[str(root)],
    binaries=[],
    datas=[],
    hiddenimports=["tkinter"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="DexKeeper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
)

app = BUNDLE(
    exe,
    name="DexKeeper.app",
    icon=str(icon_path) if icon_path.exists() else None,
    bundle_identifier="com.dexkeeper.bot",
)
