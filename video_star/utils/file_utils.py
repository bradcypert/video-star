"""Output path construction and safe filename helpers."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def safe_stem(name: str) -> str:
    """Strip characters that are unsafe in directory/file names."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name.strip(". ")[:80] or "output"


def make_output_dir(base_dir: Path, video_path: Path) -> Path:
    """Create and return a timestamped output directory for a video."""
    stem = safe_stem(video_path.stem)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = base_dir / f"{stem}_{timestamp}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "thumbnails").mkdir(exist_ok=True)
    return out
