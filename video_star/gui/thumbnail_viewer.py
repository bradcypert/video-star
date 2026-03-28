"""Grid viewer for thumbnail candidate images."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import customtkinter as ctk

try:
    from PIL import Image
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


_THUMB_SIZE = (192, 108)  # 16:9 preview


class ThumbnailViewer(ctk.CTkScrollableFrame):
    def __init__(self, parent: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self._images: list = []  # keep refs to prevent GC

    def load_thumbnails(self, paths: list[Path]) -> None:
        # Clear existing
        for widget in self.winfo_children():
            widget.destroy()
        self._images.clear()

        if not paths:
            ctk.CTkLabel(self, text="No thumbnails generated.").pack(pady=20)
            return

        if not _PIL_AVAILABLE:
            ctk.CTkLabel(
                self,
                text="Install Pillow to preview thumbnails:\n  pip install Pillow",
            ).pack(pady=20)
            return

        cols = 3
        for idx, path in enumerate(paths):
            if not path.exists():
                continue
            try:
                img = Image.open(path)
                img.thumbnail(_THUMB_SIZE)
                ctk_img = ctk.CTkImage(img, size=img.size)
                self._images.append(ctk_img)

                cell = ctk.CTkFrame(self)
                row, col = divmod(idx, cols)
                cell.grid(row=row, column=col, padx=6, pady=6)

                btn = ctk.CTkButton(
                    cell,
                    image=ctk_img,
                    text="",
                    width=img.size[0],
                    height=img.size[1],
                    fg_color="transparent",
                    hover_color=("gray80", "gray30"),
                    command=lambda p=path: _open_file(p),
                )
                btn.pack()
                ctk.CTkLabel(
                    cell, text=path.name, font=ctk.CTkFont(size=10), wraplength=200
                ).pack()
            except Exception:
                pass


def _open_file(path: Path) -> None:
    """Open an image in the system default viewer."""
    try:
        if sys.platform == "win32":
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass
