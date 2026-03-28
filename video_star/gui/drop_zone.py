"""Drag-and-drop / file-picker widget."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

_ACCEPTED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}


class DropZone(ctk.CTkFrame):
    """A bordered area that accepts dragged video files or a click-to-browse."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        on_file_selected: Callable[[Path], None],
        **kwargs,
    ) -> None:
        super().__init__(parent, **kwargs)
        self._callback = on_file_selected
        self._build_ui()
        self._wire_dnd()

    def _build_ui(self) -> None:
        self.configure(
            border_width=2,
            border_color=("gray60", "gray40"),
            fg_color=("gray92", "gray16"),
            cursor="hand2",
        )
        self._icon = ctk.CTkLabel(
            self, text="🎬", font=ctk.CTkFont(size=40)
        )
        self._icon.pack(pady=(24, 4))

        self._label = ctk.CTkLabel(
            self,
            text="Drop a video file here\nor click to browse",
            font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray60"),
        )
        self._label.pack(pady=(0, 8))

        self._detail = ctk.CTkLabel(
            self,
            text="Supported: .mp4  .mov  .mkv  .avi  .webm",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray50"),
        )
        self._detail.pack(pady=(0, 20))

        # Click anywhere in the zone to open file dialog
        for widget in (self, self._icon, self._label, self._detail):
            widget.bind("<Button-1>", self._on_click)

    def _wire_dnd(self) -> None:
        """Register drag-and-drop handlers if tkinterdnd2 is available."""
        try:
            self.drop_target_register("DND_Files")  # type: ignore[attr-defined]
            self.dnd_bind("<<Drop>>", self._on_drop)  # type: ignore[attr-defined]
        except (AttributeError, Exception):
            # tkinterdnd2 not installed or root window is not TkinterDnD.Tk
            pass

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_click(self, _event=None) -> None:
        path_str = filedialog.askopenfilename(
            title="Select video file",
            filetypes=[
                ("Video files", "*.mp4 *.mov *.mkv *.avi *.webm *.m4v"),
                ("All files", "*.*"),
            ],
        )
        if path_str:
            self._accept(Path(path_str))

    def _on_drop(self, event) -> None:
        raw = event.data.strip()
        # tkinterdnd2 may wrap paths in braces on Windows
        if raw.startswith("{") and raw.endswith("}"):
            raw = raw[1:-1]
        self._accept(Path(raw))

    def _accept(self, path: Path) -> None:
        if path.suffix.lower() not in _ACCEPTED_EXTENSIONS:
            self.set_status(
                f"Unsupported file type: {path.suffix}. "
                "Please choose a .mp4, .mov, .mkv, .avi, or .webm file.",
                error=True,
            )
            return
        self.set_file(path)
        self._callback(path)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def set_file(self, path: Path) -> None:
        size_mb = path.stat().st_size / (1024 * 1024)
        self._label.configure(
            text=f"✓ {path.name}",
            text_color=("gray10", "gray90"),
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._detail.configure(text=f"{size_mb:.1f} MB  •  {path.suffix.upper()}")

    def set_status(self, msg: str, error: bool = False) -> None:
        color = "red" if error else ("gray40", "gray60")
        self._label.configure(text=msg, text_color=color, font=ctk.CTkFont(size=13))
