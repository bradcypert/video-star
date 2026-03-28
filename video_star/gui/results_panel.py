"""Tabbed results panel showing all generated outputs."""

from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path

import customtkinter as ctk

from video_star.gui.thumbnail_viewer import ThumbnailViewer
from video_star.models.pipeline_result import PipelineResult


class ResultsPanel(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self._tabs = ctk.CTkTabview(self)
        self._tabs.pack(fill="both", expand=True, padx=4, pady=4)
        self._tab_refs: dict[str, ctk.CTkTextbox | ThumbnailViewer] = {}
        self._result: PipelineResult | None = None
        self._written: dict[str, Path] = {}

        for name in ("Description", "Chapters", "SRT", "Show Notes", "Thumbnails"):
            self._tabs.add(name)
            if name == "Thumbnails":
                viewer = ThumbnailViewer(self._tabs.tab(name))
                viewer.pack(fill="both", expand=True)
                self._tab_refs[name] = viewer
            else:
                frame = ctk.CTkFrame(self._tabs.tab(name), fg_color="transparent")
                frame.pack(fill="both", expand=True)
                frame.rowconfigure(0, weight=1)
                frame.columnconfigure(0, weight=1)

                box = ctk.CTkTextbox(frame, wrap="word", state="disabled")
                box.grid(row=0, column=0, sticky="nsew")
                self._tab_refs[name] = box

                btn_row = ctk.CTkFrame(frame, fg_color="transparent")
                btn_row.grid(row=1, column=0, sticky="ew", pady=4)
                ctk.CTkButton(
                    btn_row,
                    text="Copy to Clipboard",
                    command=lambda n=name: self._copy(n),
                    width=140,
                ).pack(side="left", padx=6)
                ctk.CTkButton(
                    btn_row,
                    text="Open File",
                    command=lambda n=name: self._open_file(n),
                    width=100,
                ).pack(side="left", padx=6)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def load_result(self, result: PipelineResult, written: dict[str, Path]) -> None:
        self._result = result
        self._written = written

        self._set_text("Description", result.description_content)
        self._set_text("Chapters", result.chapters_content)
        self._set_text("SRT", result.srt_content)
        self._set_text("Show Notes", result.show_notes_content)

        viewer = self._tab_refs.get("Thumbnails")
        if isinstance(viewer, ThumbnailViewer):
            viewer.load_thumbnails(result.thumbnail_paths)

    def clear(self) -> None:
        for name, widget in self._tab_refs.items():
            if isinstance(widget, ctk.CTkTextbox):
                widget.configure(state="normal")
                widget.delete("1.0", "end")
                widget.configure(state="disabled")
            elif isinstance(widget, ThumbnailViewer):
                widget.load_thumbnails([])

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_text(self, tab: str, content: str) -> None:
        box = self._tab_refs.get(tab)
        if isinstance(box, ctk.CTkTextbox):
            box.configure(state="normal")
            box.delete("1.0", "end")
            box.insert("1.0", content or "(no content generated)")
            box.configure(state="disabled")

    def _copy(self, tab: str) -> None:
        box = self._tab_refs.get(tab)
        if isinstance(box, ctk.CTkTextbox):
            content = box.get("1.0", "end").strip()
            root = self.winfo_toplevel()
            root.clipboard_clear()
            root.clipboard_append(content)

    def _open_file(self, tab: str) -> None:
        key_map = {
            "Description": "description",
            "Chapters": "chapters",
            "SRT": "srt",
            "Show Notes": "show_notes",
        }
        key = key_map.get(tab)
        path = self._written.get(key) if key else None
        if path and path.exists():
            try:
                if sys.platform == "win32":
                    os.startfile(str(path))
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(path)])
                else:
                    subprocess.Popen(["xdg-open", str(path)])
            except Exception:
                pass
