"""Deepgram transcription wrapper.

Uses the PrerecordedOptions + listen.rest.v("1").transcribe_file() API,
which is the correct full-featured path in deepgram-sdk v3 through v6.
listen.rest was introduced in v3; v3 also exposes listen.prerecorded as
an alias, which we fall back to if rest is absent.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Callable

from deepgram import DeepgramClient, PrerecordedOptions


class TranscriptionError(Exception):
    pass


_MAX_RETRIES = 3

_OPTIONS = PrerecordedOptions(
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

    Retries up to _MAX_RETRIES times on network errors with exponential backoff.
    """
    if not api_key:
        raise TranscriptionError("Deepgram API key is not configured.")

    client = DeepgramClient(api_key=api_key)

    # listen.rest is the canonical name (v3+); listen.prerecorded is the older alias.
    endpoint = getattr(client.listen, "rest", None) or client.listen.prerecorded

    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    if on_log:
        on_log(f"Audio file size: {file_size_mb:.1f} MB")
    if file_size_mb > 500 and on_log:
        on_log(
            f"Warning: audio file is large ({file_size_mb:.0f} MB). "
            "Upload may take several minutes."
        )

    audio_bytes = audio_path.read_bytes()
    payload = {"buffer": audio_bytes}

    last_exc: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            if on_log:
                on_log(f"Uploading audio to Deepgram (attempt {attempt}/{_MAX_RETRIES})…")
            response = endpoint.v("1").transcribe_file(payload, _OPTIONS)
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


def _to_dict(response: object) -> dict:
    """Normalise a Deepgram SDK response to a plain Python dict."""
    if isinstance(response, dict):
        return response
    if hasattr(response, "to_json"):           # v3–v6 preferred path
        return json.loads(response.to_json())
    if hasattr(response, "to_dict"):           # older fallback
        return response.to_dict()
    if hasattr(response, "model_dump"):        # Pydantic v2
        return response.model_dump()
    if hasattr(response, "dict"):              # Pydantic v1
        return response.dict()
    raise TranscriptionError(
        f"Cannot convert Deepgram response to dict: {type(response)}"
    )
