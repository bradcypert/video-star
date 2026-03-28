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
from PyInstaller.utils.hooks import collect_all

# ── Collect packages that use complex internal import chains ──────────────────
# PyInstaller's static analysis only follows the top-level __init__.py; these
# packages re-export symbols from deep submodules that get missed.  collect_all
# recursively gathers every submodule, data file, and binary in the tree.

datas: list = []
binaries: list = []
_hidden: list = []

for _pkg in ("deepgram", "openai"):
    _d, _b, _h = collect_all(_pkg)
    datas += _d
    binaries += _b
    _hidden += _h

# ── Locate GUI package data ────────────────────────────────────────────────────

import customtkinter
datas.append((str(Path(customtkinter.__file__).parent), "customtkinter"))

try:
    import tkinterdnd2
    datas.append((str(Path(tkinterdnd2.__file__).parent), "tkinterdnd2"))
    _hidden.append("tkinterdnd2")
except ImportError:
    pass  # drag-and-drop is optional

# ── Additional hidden imports ─────────────────────────────────────────────────

_hidden += [
    "customtkinter",
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "PIL.ImageFont",
    "dotenv",
]

# ── Analysis ───────────────────────────────────────────────────────────────────

a = Analysis(
    [str(Path("video_star") / "__main__.py")],
    pathex=[str(Path(".").resolve())],
    binaries=binaries,
    datas=datas,
    hiddenimports=_hidden,
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
