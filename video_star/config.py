"""Settings loader.

API keys are stored in ~/.video-star/.env so they never land in the project
directory and are preserved across reinstalls.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv, set_key

_ENV_DIR = Path.home() / ".video-star"
_ENV_FILE = _ENV_DIR / ".env"


def _load() -> None:
    """Load the user env file, then let real env vars override."""
    _ENV_DIR.mkdir(parents=True, exist_ok=True)
    if not _ENV_FILE.exists():
        _ENV_FILE.touch()
    load_dotenv(_ENV_FILE, override=False)


_load()


class ConfigError(Exception):
    pass


def _int_env(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


class Settings:
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OUTPUT_DIR: Path = Path(
        os.path.expanduser(os.getenv("OUTPUT_DIR", "~/Videos/video-star-output"))
    )
    FFMPEG_PATH: str = os.getenv("FFMPEG_PATH", "")
    THUMBNAIL_COUNT: int = _int_env("THUMBNAIL_COUNT", 5)
    USE_THUMBNAIL_OVERLAY: bool = os.getenv("USE_THUMBNAIL_OVERLAY", "false").lower() == "true"
    USE_OPENAI_DESCRIPTION: bool = bool(os.getenv("OPENAI_API_KEY", ""))

    @classmethod
    def reload(cls) -> None:
        """Re-read the env file (call after saving settings)."""
        load_dotenv(_ENV_FILE, override=True)
        cls.DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
        cls.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        cls.OUTPUT_DIR = Path(
            os.path.expanduser(os.getenv("OUTPUT_DIR", "~/Videos/video-star-output"))
        )
        cls.FFMPEG_PATH = os.getenv("FFMPEG_PATH", "")
        cls.THUMBNAIL_COUNT = _int_env("THUMBNAIL_COUNT", 5)
        cls.USE_THUMBNAIL_OVERLAY = (
            os.getenv("USE_THUMBNAIL_OVERLAY", "false").lower() == "true"
        )
        cls.USE_OPENAI_DESCRIPTION = bool(os.getenv("OPENAI_API_KEY", ""))

    @classmethod
    def needs_setup(cls) -> bool:
        return not cls.DEEPGRAM_API_KEY.strip()

    @classmethod
    def validate(cls) -> None:
        if not cls.DEEPGRAM_API_KEY.strip():
            raise ConfigError(
                "DEEPGRAM_API_KEY is not set. Open Settings to add your key."
            )

    @classmethod
    def save(cls, **kwargs: str) -> None:
        """Persist key=value pairs to ~/.video-star/.env."""
        _ENV_DIR.mkdir(parents=True, exist_ok=True)
        if not _ENV_FILE.exists():
            _ENV_FILE.touch()
        for key, value in kwargs.items():
            set_key(str(_ENV_FILE), key, value)
        cls.reload()
