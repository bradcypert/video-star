"""Root application window."""

from __future__ import annotations

import sys
from pathlib import Path

import customtkinter as ctk

from video_star.config import Settings
from video_star.core.pipeline import PipelineCallbacks, PipelineRunner
from video_star.gui.drop_zone import DropZone
from video_star.gui.progress_panel import ProgressPanel
from video_star.gui.results_panel import ResultsPanel
from video_star.gui.settings_dialog import SettingsDialog
from video_star.models.pipeline_result import PipelineResult

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


def _make_root() -> ctk.CTk:
    """Create the root window, using TkinterDnD if available."""
    try:
        from tkinterdnd2 import TkinterDnD

        class _DnDCTk(ctk.CTk, TkinterDnD.DnDWrapper):
            def __init__(self) -> None:
                super().__init__()
                self.TkdndVersion = TkinterDnD._require(self)

        return _DnDCTk()
    except Exception:
        return ctk.CTk()


class App:
    def __init__(self) -> None:
        self._root = _make_root()
        self._root.title("video-star")
        self._root.geometry("860x760")
        self._root.minsize(700, 600)

        self._video_path: Path | None = None
        self._running = False

        self._build_ui()

        if Settings.needs_setup():
            self._root.after(200, self._open_settings)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # Header
        header = ctk.CTkFrame(self._root, height=50, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text="⭐ video-star",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=16)
        ctk.CTkButton(
            header,
            text="⚙ Settings",
            width=110,
            command=self._open_settings,
        ).pack(side="right", padx=12, pady=8)

        # Drop zone
        self._drop_zone = DropZone(
            self._root,
            on_file_selected=self._on_file_selected,
            height=140,
        )
        self._drop_zone.pack(fill="x", padx=16, pady=(12, 0))

        # Process button
        self._process_btn = ctk.CTkButton(
            self._root,
            text="Process Video",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=44,
            command=self._on_process,
            state="disabled",
        )
        self._process_btn.pack(padx=16, pady=10)

        # Progress
        self._progress = ProgressPanel(self._root, height=160)
        self._progress.pack(fill="x", padx=16)

        # Results
        self._results = ResultsPanel(self._root)
        self._results.pack(fill="both", expand=True, padx=16, pady=(8, 12))

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_file_selected(self, path: Path) -> None:
        self._video_path = path
        self._process_btn.configure(state="normal")
        self._results.clear()
        self._progress.reset()

    def _on_process(self) -> None:
        if self._running or not self._video_path:
            return
        if Settings.needs_setup():
            self._open_settings()
            return

        self._running = True
        self._process_btn.configure(state="disabled", text="Processing…")
        self._progress.reset()
        self._results.clear()

        callbacks = PipelineCallbacks(
            on_stage=lambda s, p: self._root.after(0, self._progress.set_stage, s, p),
            on_log=lambda msg: self._root.after(0, self._progress.append_log, msg),
            on_complete=lambda r, w: self._root.after(0, self._on_complete, r, w),
            on_error=lambda e: self._root.after(0, self._on_error, e),
        )

        runner = PipelineRunner(Settings, callbacks)
        runner.run_async(self._video_path)

    def _on_complete(self, result: PipelineResult, written: dict) -> None:
        self._running = False
        self._process_btn.configure(state="normal", text="Process Video")
        self._results.load_result(result, written)
        self._progress.append_log(
            f"\nAll outputs written to:\n  {result.output_dir}"
        )

    def _on_error(self, exc: Exception) -> None:
        self._running = False
        self._process_btn.configure(state="normal", text="Process Video")
        self._progress.set_stage(f"Error: {exc}", 0)
        self._progress.append_log(f"\nERROR: {exc}")

    def _open_settings(self) -> None:
        SettingsDialog(self._root)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self) -> None:
        self._root.mainloop()
