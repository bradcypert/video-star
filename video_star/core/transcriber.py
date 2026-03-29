"""Deepgram transcription wrapper.

Supports deepgram-sdk v3/v4/v5 (PrerecordedOptions style) and
v6+ (Fern-generated, keyword-argument style) via runtime detection.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Callable

from deepgram import DeepgramClient


class TranscriptionError(Exception):
    pass


_MAX_RETRIES = 3

# Options forwarded to the Deepgram API regardless of SDK version.
_OPTIONS = dict(
    model="nova-2",
    smart_format=True,
    punctuate=True,
    paragraphs=True,
    utterances=True,
    diarize=True,
    summarize="v2",
    detect_topics=True,
    language="en-US",
)


def transcribe(
    audio_path: Path,
    api_key: str,
    on_log: Callable[[str], None] | None = None,
) -> dict:
    """Upload *audio_path* to Deepgram and return the raw response as a dict.

    Retries up to ``_MAX_RETRIES`` times on network errors with exponential
    backoff.
    """
    if not api_key:
        raise TranscriptionError("Deepgram API key is not configured.")

    client = DeepgramClient(api_key)

    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    if on_log:
        on_log(f"Audio file size: {file_size_mb:.1f} MB")
    if file_size_mb > 500 and on_log:
        on_log(
            f"Warning: audio file is large ({file_size_mb:.0f} MB). "
            "Upload may take several minutes."
        )

    audio_bytes = audio_path.read_bytes()

    last_exc: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            if on_log:
                on_log(f"Uploading audio to Deepgram (attempt {attempt}/{_MAX_RETRIES})…")
            response = _call_api(client, audio_bytes)
            if on_log:
                on_log("Transcription complete.")
            return _to_dict(response)
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


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _call_api(client: DeepgramClient, audio_bytes: bytes) -> object:
    """Dispatch to the correct SDK generation's transcription method."""
    # SDK v6+ (Fern-generated): options are keyword arguments.
    # client.listen.v1.media.transcribe_file(request=<bytes>, model=..., ...)
    v1_media = (
        getattr(getattr(client.listen, "v1", None), "media", None)
    )
    if v1_media is not None:
        return v1_media.transcribe_file(request=audio_bytes, **_OPTIONS)

    # SDK v3–v5: PrerecordedOptions object.
    # listen.rest (v4–v5) or listen.prerecorded (v3).
    from deepgram import PrerecordedOptions  # noqa: PLC0415
    options = PrerecordedOptions(**_OPTIONS)
    payload = {"buffer": audio_bytes}
    endpoint = getattr(client.listen, "rest", None) or client.listen.prerecorded
    return endpoint.v("1").transcribe_file(payload, options)


def _to_dict(response: object) -> dict:
    """Normalise any SDK response object to a plain Python dict."""
    if isinstance(response, dict):
        return response
    # v6 Fern responses expose to_json() → JSON string
    if hasattr(response, "to_json"):
        return json.loads(response.to_json())
    # v3–v5 responses expose to_dict()
    if hasattr(response, "to_dict"):
        return response.to_dict()
    # Pydantic v2
    if hasattr(response, "model_dump"):
        return response.model_dump()
    # Pydantic v1
    if hasattr(response, "dict"):
        return response.dict()
    raise TranscriptionError(
        f"Cannot convert Deepgram response to dict: {type(response)}"
    )
