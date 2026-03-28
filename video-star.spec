# video-star.spec
#
# PyInstaller spec file for video-star.
# Run from the repo root: pyinstaller video-star.spec
#
# Required packages must be installed before building:
#   pip install -e .
#   pip install pyinstaller

import sys
import os
from pathlib import Path

# ── Locate package data that PyInstaller won't find automatically ──────────────

import customtkinter
CTK_PATH = Path(customtkinter.__file__).parent

datas = [
    (str(CTK_PATH), "customtkinter"),
]

try:
    import tkinterdnd2
    TKDND_PATH = Path(tkinterdnd2.__file__).parent
    datas.append((str(TKDND_PATH), "tkinterdnd2"))
except ImportError:
    pass  # drag-and-drop optional

# ── Analysis ───────────────────────────────────────────────────────────────────

a = Analysis(
    [str(Path("video_star") / "__main__.py")],
    pathex=[str(Path(".").resolve())],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "customtkinter",
        "tkinterdnd2",
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
        "PIL.ImageFont",
        "deepgram",
        "openai",
        "dotenv",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

# Optional icon
_icon_path = Path("assets") / "icon.ico"
_icon = str(_icon_path) if _icon_path.exists() else None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="video-star",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # windowed — no terminal window on double-click
    icon=_icon,
)
