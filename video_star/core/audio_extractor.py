"""Extract audio from a video file using ffmpeg."""

from __future__ import annotations

import io
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Callable

from video_star.utils.ffmpeg_utils import find_ffmpeg, find_ffprobe, probe_duration


class AudioExtractionError(Exception):
    pass


def extract_audio(
    video_path: Path,
    ffmpeg_path: str = "",
    on_progress: Callable[[float], None] | None = None,
) -> Path:
    """Extract audio from *video_path* to a temporary 16 kHz mono WAV file.

    Returns the path to the WAV file.  The caller is responsible for deleting
    it when finished.
    """
    ffmpeg = find_ffmpeg(ffmpeg_path)

    try:
        ffprobe = find_ffprobe(ffmpeg)
        duration = probe_duration(video_path, ffprobe)
    except Exception as exc:
        raise AudioExtractionError(f"Could not probe video file: {exc}") from exc

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    out_path = Path(tmp.name)

    cmd = [
        ffmpeg,
        "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-progress", "pipe:1",
        str(out_path),
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Drain stderr in a background thread to prevent pipe-buffer deadlock.
    # ffmpeg is verbose; if we don't read stderr while also reading stdout
    # the OS pipe buffer fills and the subprocess blocks.
    stderr_buf = io.StringIO()

    def _drain_stderr() -> None:
        assert process.stderr is not None
        for line in process.stderr:
            stderr_buf.write(line)

    stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
    stderr_thread.start()

    if on_progress:
        assert process.stdout is not None
        for line in process.stdout:
            line = line.strip()
            if line.startswith("out_time_ms="):
                try:
                    elapsed_ms = int(line.split("=", 1)[1])
                    elapsed_s = elapsed_ms / 1_000_000
                    on_progress(min(elapsed_s / duration, 1.0))
                except (ValueError, ZeroDivisionError):
                    pass

    process.wait()
    stderr_thread.join(timeout=5)

    if process.returncode != 0:
        stderr = stderr_buf.getvalue()
        out_path.unlink(missing_ok=True)
        raise AudioExtractionError(
            f"ffmpeg exited with code {process.returncode}:\n{stderr}"
        )

    if on_progress:
        on_progress(1.0)

    return out_path
