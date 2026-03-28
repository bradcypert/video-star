"""Progress bar and scrolling log panel."""

from __future__ import annotations

import customtkinter as ctk


class ProgressPanel(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self._build_ui()

    def _build_ui(self) -> None:
        self._stage_label = ctk.CTkLabel(
            self, text="Ready.", anchor="w", font=ctk.CTkFont(size=12)
        )
        self._stage_label.pack(fill="x", padx=12, pady=(8, 2))

        self._bar = ctk.CTkProgressBar(self)
        self._bar.set(0)
        self._bar.pack(fill="x", padx=12, pady=(0, 6))

        self._log = ctk.CTkTextbox(self, height=100, state="disabled", wrap="word")
        self._log.pack(fill="both", expand=True, padx=12, pady=(0, 8))

    def set_stage(self, label: str, progress: float) -> None:
        self._stage_label.configure(text=label)
        self._bar.set(max(0.0, min(1.0, progress)))

    def append_log(self, msg: str) -> None:
        self._log.configure(state="normal")
        self._log.insert("end", msg + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def reset(self) -> None:
        self._stage_label.configure(text="Ready.")
        self._bar.set(0)
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")
