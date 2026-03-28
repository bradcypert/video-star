# video-star ⭐

A desktop post-production pipeline for YouTube creators.  Drop in your edited
video and get back:

| Output | File |
|---|---|
| Full transcript (SRT subtitles) | `transcript.srt` |
| Plain-text transcript (with speaker labels) | `transcript.txt` |
| YouTube chapter timestamps | `chapters.txt` |
| Video description + SEO hashtags | `description.txt` |
| Markdown show notes | `show_notes.md` |
| Thumbnail candidate frames | `thumbnails/*.jpg` |
| Raw Deepgram JSON (for offline re-processing) | `raw_deepgram.json` |

Powered by **Deepgram Nova-2** for transcription, summarisation, topic
detection and chapter generation.  Optionally uses **OpenAI GPT-4o** for
richer YouTube descriptions.

---

## Requirements

- **Python 3.10+**
- **ffmpeg** (used for audio extraction and thumbnail frame capture)

### Windows (recommended)

```powershell
winget install Python.Python.3.12
winget install Gyan.FFmpeg
```

### macOS

```bash
brew install python@3.12 ffmpeg
```

### Linux (Debian/Ubuntu)

```bash
sudo apt install python3.12 python3.12-venv ffmpeg
```

---

## Installation

```bash
git clone https://github.com/bradcypert/video-star.git
cd video-star
pip install -e .
```

Or install directly:

```bash
pip install video-star
```

---

## First run

```bash
video-star
```

On the first launch the **Settings** dialog will open automatically.  Enter
your **Deepgram API key** (required) and optionally your **OpenAI API key**
(for AI-written descriptions).

Keys are stored in `~/.video-star/.env` — they are **never** placed in the
project directory.

### Getting API keys

- **Deepgram** — <https://console.deepgram.com/> (free tier available)
- **OpenAI** — <https://platform.openai.com/api-keys> (optional)

---

## Usage

1. Launch `video-star`
2. Drag your video onto the drop zone (or click *Browse*)
3. Click **Process Video**
4. Wait ~1–3 minutes while Deepgram transcribes (time depends on video length)
5. Review outputs in the tabbed panel:
   - **Description** — copy-paste into YouTube
   - **Chapters** — paste at the bottom of the description
   - **SRT** — upload as closed captions
   - **Show Notes** — publish as a blog post or podcast episode notes
   - **Thumbnails** — click any frame to open it in your image editor
6. All files are saved to your configured **Output Directory**

---

## Configuration

Open **Settings** (⚙ button, top-right) to configure:

| Setting | Default | Description |
|---|---|---|
| Deepgram API Key | — | Required |
| OpenAI API Key | — | Optional; enables GPT-4o descriptions |
| Output Directory | `~/Videos/video-star-output` | Where output folders are created |
| ffmpeg Path | auto-detect | Override if ffmpeg is not on PATH |
| Thumbnail Count | 5 | How many frame candidates to extract |
| Thumbnail Text Overlay | off | Draw chapter title text on frames |

---

## Development

```bash
pip install -e ".[dev]"    # or: pip install -r requirements-dev.txt
pytest                     # run tests
```

### Project structure

```
video_star/
├── config.py               settings loader (dotenv)
├── models/                 dataclasses (PipelineResult, Chapter, …)
├── core/
│   ├── audio_extractor.py  ffmpeg wrapper
│   ├── transcriber.py      Deepgram SDK wrapper
│   ├── post_processor.py   raw JSON → PipelineResult
│   ├── pipeline.py         orchestration + threading
│   └── output_writer.py    writes files to disk
├── generators/
│   ├── srt_generator.py
│   ├── chapters_generator.py
│   ├── description_generator.py
│   ├── show_notes_generator.py
│   └── thumbnail_extractor.py
└── gui/
    ├── app.py              root window
    ├── drop_zone.py        drag-and-drop widget
    ├── progress_panel.py   progress bar + log
    ├── results_panel.py    tabbed output viewer
    ├── settings_dialog.py  settings modal
    └── thumbnail_viewer.py image grid
```

---

## Roadmap

- [ ] PyInstaller single-file `.exe` for Windows (no Python install required)
- [ ] DALL-E / AI thumbnail generation
- [ ] Re-process from saved `raw_deepgram.json` (no API cost)
- [ ] Batch processing of multiple videos
- [ ] Export chapters directly into video metadata via ffmpeg

---

## License

MIT
