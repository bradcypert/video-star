"""Entry point: python -m video_star  or  video-star (CLI script)."""

from __future__ import annotations


def main() -> None:
    from video_star.gui.app import App

    app = App()
    app.run()


if __name__ == "__main__":
    main()
