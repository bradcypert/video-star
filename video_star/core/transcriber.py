"""Deepgram transcription — direct REST API via urllib (stdlib only).

We deliberately do NOT import deepgram-sdk here.  The SDK's Fern-generated
import chain breaks inside PyInstaller bundles regardless of collect_all,
because the generated __init__.py fails to re-export symbols from submodules
that PyInstaller's static analyser cannot follow.

Calling the REST API with urllib is simpler, has zero extra dependencies,
and produces the identical JSON response that post_processor.py already
knows how to parse.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable


class TranscriptionError(Exception):
    pass


_MAX_RETRIES = 3
_TIMEOUT_SECONDS = 600  # generous limit for long audio files

_PARAMS = urllib.parse.urlencode({
    "model": "nova-2",
    "smart_format": "true",
    "punctuate": "true",
    "paragraphs": "true",
    "utterances": "true",
    "diarize": "true",
    "summarize": "v2",
    "detect_topics": "true",
    "language": "en-US",
})

_ENDPOINT = f"https://api.deepgram.com/v1/listen?{_PARAMS}"


def transcribe(
    audio_path: Path,
    api_key: str,
    on_log: Callable[[str], None] | None = None,
) -> dict:
    """POST *audio_path* to Deepgram and return the raw response as a dict."""
    if not api_key:
        raise TranscriptionError("Deepgram API key is not configured.")

    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    if on_log:
        on_log(f"Audio file size: {file_size_mb:.1f} MB")
    if file_size_mb > 500 and on_log:
        on_log(
            f"Warning: large file ({file_size_mb:.0f} MB) — "
            "upload may take several minutes."
        )

    audio_bytes = audio_path.read_bytes()

    last_exc: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            if on_log:
                on_log(
                    f"Uploading audio to Deepgram "
                    f"(attempt {attempt}/{_MAX_RETRIES})…"
                )
            result = _post(audio_bytes, api_key)
            if on_log:
                on_log("Transcription complete.")
            return result
        except Exception as exc:
            last_exc = exc
            if on_log:
                on_log(f"Attempt {attempt} failed: {exc}")
            if attempt < _MAX_RETRIES:
                wait = 2 ** attempt
                if on_log:
                    on_log(f"Retrying in {wait}s…")
                time.sleep(wait)

    raise TranscriptionError(
        f"Transcription failed after {_MAX_RETRIES} attempts: {last_exc}"
    ) from last_exc


def _post(audio_bytes: bytes, api_key: str) -> dict:
    req = urllib.request.Request(
        _ENDPOINT,
        data=audio_bytes,
        headers={
            "Authorization": f"Token {api_key}",
            "Content-Type": "audio/wav",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise TranscriptionError(
            f"Deepgram API returned {exc.code}: {body}"
        ) from exc
