# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os

# PyInstaller does not always define __file__ in spec execution.
root = Path(os.getcwd()).resolve()
entry = root / "Sources" / "DexKeeper_Bot" / "dexkeeper_bot.py"

block_cipher = None

a = Analysis(
    [str(entry)],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(root / "assets" / "DexKeeper_Bot_icon.png"), "assets")],
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
)
