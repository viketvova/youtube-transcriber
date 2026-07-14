<div align="center">

# YouTube Transcriber

**Download any YouTube video and get a full text transcription in seconds.**

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/windows)

</div>

---

## What it does

Paste a YouTube link, pick a language, and get a clean text transcript with time markers. That's it.

**YouTube Transcriber** downloads the audio from any YouTube video, runs it through OpenAI's Whisper speech recognition model, and saves the result as a readable text file — automatically named after the video title.

### Key features

- **One-click transcription** — paste URL, click Start, get text
- **3 languages** — Russian, English, Ukrainian
- **Time range selection** — transcribe only 10:00–25:00 of a 2-hour video
- **Blender-style UI** — dark and light themes, theme remembers your choice
- **Search everywhere** — filter files, search text in preview, find-next like in Word
- **History** — all previous transcriptions are saved and browsable
- **Auto-naming** — files saved as `Video Title.txt`

---

## Quick start

### 1. Install prerequisites

| Tool | Why | Link |
|------|-----|------|
| **Python 3.8+** | Runtime | [python.org](https://www.python.org/downloads/) |
| **ffmpeg** | Audio extraction | [ffmpeg.org](https://ffmpeg.org/download.html) — add `bin/` to PATH |
| **Node.js** | YouTube video decoding | [nodejs.org](https://nodejs.org/) |

### 2. Clone & install

```bash
git clone https://github.com/viketvova/youtube-transcriber.git
cd youtube-transcriber
pip install -r requirements.txt
```

### 3. Run

```bash
python gui.py
```

That's it. No configuration needed.

---

## How it works

```
YouTube URL
    │
    ▼
┌─────────────┐
│   yt-dlp    │  Download audio stream
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   ffmpeg    │  Convert to 16kHz WAV (trim if time range set)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Whisper   │  Speech-to-text (medium model by default)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Save .txt  │  Timestamped text, named after video
└─────────────┘
```

---

## Interface

The app has 3 tabs:

| Tab | What it does |
|-----|--------------|
| **Transcribe** | Paste URL, set time range, pick language/model, start transcription |
| **History** | Browse all previous transcriptions, search files, preview with find-next |
| **Settings** | Switch between Dark and Light themes |

---

## CLI mode

For power users who prefer the terminal:

```bash
# Basic
python transcribe.py https://www.youtube.com/watch?v=XXXXX

# Time range
python transcribe.py https://www.youtube.com/watch?v=XXXXX --start 01:30:00 --end 02:00:00

# Custom output
python transcribe.py https://www.youtube.com/watch?v=XXXXX -o notes.txt

# Better accuracy (slower)
python transcribe.py https://www.youtube.com/watch?v=XXXXX --model large
```

| Option | Default | Description |
|--------|---------|-------------|
| `--model` | medium | tiny / base / small / medium / large |
| `--language` | ru | ru / en / uk |
| `--start` | 0 | Start time (HH:MM:SS) |
| `--end` | full | End time (HH:MM:SS) |
| `--chunk` | 5 | Minutes per output block |

---

## Model comparison

| Model | Size | Speed | Best for |
|-------|------|-------|----------|
| `tiny` | 39 MB | ~1 min / 30min video | Quick preview |
| `small` | 244 MB | ~3 min | Good balance |
| **`medium`** | **769 MB** | **~12 min** | **Best overall** |
| `large` | 1.5 GB | ~25 min | Maximum accuracy |

---

## Output example

```
============================================================
TRANSCRIPTION
Source: https://www.youtube.com/watch?v=XXXXX
Language: English
Segments: 84
============================================================

[00:00:00 - 00:05:00]
Hey everyone, today we're going to talk about the latest update to the platform and what it means for creators...

[00:05:00 - 00:10:00]
As you can see on screen, the first step is to open the settings menu and navigate to the new dashboard...

[00:10:00 - 00:15:00]
This feature has been requested by the community for months, and I'm really excited to finally show you how it works...

============================================================
END OF TRANSCRIPTION
============================================================
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ffmpeg not found` | Install ffmpeg, add `bin/` to system PATH |
| Download fails (403) | Install Node.js — required for YouTube video extraction |
| CUDA out of memory | Use `--device cpu` or `--model small` |
| Slow transcription | Use GPU (`--device cuda`) or smaller model |

---

## License

[MIT](LICENSE) — use it however you want.
