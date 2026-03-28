"""Deepgram transcription wrapper."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from deepgram import DeepgramClient, PrerecordedOptions


class TranscriptionError(Exception):
    pass


_MAX_RETRIES = 3


def transcribe(
    audio_path: Path,
    api_key: str,
    on_log: Callable[[str], None] | None = None,
) -> dict:
    """Upload *audio_path* to Deepgram and return the raw response dict.

    Retries up to ``_MAX_RETRIES`` times on network errors with exponential
    backoff.
    """
    if not api_key:
        raise TranscriptionError("Deepgram API key is not configured.")

    client = DeepgramClient(api_key)

    options = PrerecordedOptions(
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

    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    if on_log:
        on_log(f"Audio file size: {file_size_mb:.1f} MB")
    if file_size_mb > 500:
        if on_log:
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
                on_log(
                    f"Uploading audio to Deepgram (attempt {attempt}/{_MAX_RETRIES})…"
                )
            response = client.listen.prerecorded.v("1").transcribe_file(
                payload, options
            )
            if on_log:
                on_log("Transcription complete.")
            # Return the raw dict so it can be saved and re-processed offline
            return response.to_dict()
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
