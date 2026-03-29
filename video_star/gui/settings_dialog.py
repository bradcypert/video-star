"""Settings dialog for API keys and preferences."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from video_star.config import Settings


def _validate_deepgram_key(api_key: str) -> None:
    """Ping the Deepgram API to confirm the key is valid.

    Uses a raw HTTP request so it is not coupled to any SDK version.
    """
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        "https://api.deepgram.com/v1/projects",
        headers={"Authorization": f"Token {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status not in (200, 201):
                raise ValueError(f"Unexpected status {resp.status}")
    except urllib.error.HTTPError as exc:
        raise ValueError(f"HTTP {exc.code}: invalid key or no permissions") from exc


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)
        self.title("Settings")
        self.geometry("520x520")
        self.resizable(False, False)
        self.grab_set()  # modal

        self._build_ui()
        self._load_values()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        pad = {"padx": 16, "pady": 6}

        ctk.CTkLabel(self, text="Settings", font=ctk.CTkFont(size=18, weight="bold")).pack(
            pady=(16, 4)
        )

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", **pad)
        form.columnconfigure(1, weight=1)

        row = 0

        def _label(text: str) -> None:
            nonlocal row
            ctk.CTkLabel(form, text=text, anchor="w").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=4
            )

        def _entry(show: str = "") -> ctk.CTkEntry:
            nonlocal row
            e = ctk.CTkEntry(form, show=show, width=300)
            e.grid(row=row, column=1, sticky="ew", pady=4)
            row += 1
            return e

        _label("Deepgram API Key *")
        self._dg_key = _entry(show="•")

        _label("OpenAI API Key (optional)")
        self._oai_key = _entry(show="•")

        _label("Output Directory")
        row_out = row
        row += 1
        out_frame = ctk.CTkFrame(form, fg_color="transparent")
        out_frame.grid(row=row_out, column=1, sticky="ew", pady=4)
        out_frame.columnconfigure(0, weight=1)
        self._out_dir = ctk.CTkEntry(out_frame)
        self._out_dir.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(out_frame, text="Browse", width=70, command=self._browse_output).grid(
            row=0, column=1, padx=(6, 0)
        )

        _label("ffmpeg Path (optional)")
        row_ff = row
        row += 1
        ff_frame = ctk.CTkFrame(form, fg_color="transparent")
        ff_frame.grid(row=row_ff, column=1, sticky="ew", pady=4)
        ff_frame.columnconfigure(0, weight=1)
        self._ffmpeg_path = ctk.CTkEntry(ff_frame, placeholder_text="auto-detect")
        self._ffmpeg_path.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(ff_frame, text="Browse", width=70, command=self._browse_ffmpeg).grid(
            row=0, column=1, padx=(6, 0)
        )

        _label("Thumbnail Count")
        row += 1
        self._thumb_count = ctk.CTkSlider(form, from_=1, to=10, number_of_steps=9)
        self._thumb_count.grid(row=row - 1, column=1, sticky="ew", pady=4)

        _label("Thumbnail Text Overlay")
        row += 1
        self._overlay_var = tk.BooleanVar(value=False)
        ctk.CTkSwitch(form, text="", variable=self._overlay_var).grid(
            row=row - 1, column=1, sticky="w", pady=4
        )

        # Status / test button
        self._status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self._status_label.pack(pady=(4, 0))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=12)
        ctk.CTkButton(btn_frame, text="Test Deepgram Connection", command=self._test_connection).pack(
            side="left", padx=6
        )
        ctk.CTkButton(btn_frame, text="Save", command=self._save).pack(side="left", padx=6)
        ctk.CTkButton(
            btn_frame, text="Cancel", fg_color="gray", command=self.destroy
        ).pack(side="left", padx=6)

    def _load_values(self) -> None:
        self._dg_key.insert(0, Settings.DEEPGRAM_API_KEY)
        self._oai_key.insert(0, Settings.OPENAI_API_KEY)
        self._out_dir.insert(0, str(Settings.OUTPUT_DIR))
        self._ffmpeg_path.insert(0, Settings.FFMPEG_PATH)
        self._thumb_count.set(float(Settings.THUMBNAIL_COUNT))
        self._overlay_var.set(Settings.USE_THUMBNAIL_OVERLAY)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _browse_output(self) -> None:
        d = filedialog.askdirectory(title="Select output directory")
        if d:
            self._out_dir.delete(0, "end")
            self._out_dir.insert(0, d)

    def _browse_ffmpeg(self) -> None:
        f = filedialog.askopenfilename(
            title="Select ffmpeg binary",
            filetypes=[("Executable", "*.exe ffmpeg"), ("All files", "*.*")],
        )
        if f:
            self._ffmpeg_path.delete(0, "end")
            self._ffmpeg_path.insert(0, f)

    def _test_connection(self) -> None:
        key = self._dg_key.get().strip()
        if not key:
            self._set_status("Enter a Deepgram API key first.", "red")
            return
        self._set_status("Testing connection…", "gray")

        def _run() -> None:
            try:
                _validate_deepgram_key(key)
                msg, color = "✓ Connected to Deepgram!", "green"
            except Exception as exc:
                msg, color = f"Connection failed: {exc}", "red"

            # The dialog may have been closed while the thread was running.
            try:
                self.after(0, lambda: self._set_status(msg, color))
            except Exception:
                pass

        threading.Thread(target=_run, daemon=True).start()

    def _save(self) -> None:
        Settings.save(
            DEEPGRAM_API_KEY=self._dg_key.get().strip(),
            OPENAI_API_KEY=self._oai_key.get().strip(),
            OUTPUT_DIR=self._out_dir.get().strip(),
            FFMPEG_PATH=self._ffmpeg_path.get().strip(),
            THUMBNAIL_COUNT=str(int(self._thumb_count.get())),
            USE_THUMBNAIL_OVERLAY=str(self._overlay_var.get()).lower(),
        )
        self._set_status("Settings saved.", "green")
        self.after(800, self.destroy)

    def _set_status(self, msg: str, color: str = "gray") -> None:
        self._status_label.configure(text=msg, text_color=color)
