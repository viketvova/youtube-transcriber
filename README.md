# YouTube Transcriber

Download YouTube videos and transcribe speech to text with time markers. Supports Russian, English, and Ukrainian.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- Download audio from YouTube videos
- Transcribe speech using OpenAI Whisper (via faster-whisper)
- Time range selection — transcribe only a specific segment
- Dark/Light theme toggle
- Search through transcriptions
- History of previous transcriptions
- Export to text file with time markers

## Installation

### Prerequisites

- Python 3.8+
- [ffmpeg](https://ffmpeg.org/download.html) installed and in PATH
- Node.js (for yt-dlp YouTube extraction)

### Setup

```bash
# Clone the repository
git clone https://github.com/your-username/youtube-transcriber.git
cd youtube-transcriber

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## Usage

### GUI Mode

```bash
python gui.py
```

1. Paste a YouTube URL
2. Select language (Russian/English/Ukrainian)
3. Optionally set time range (From/To)
4. Click "Start Transcription"
5. View results in the Result tab

### CLI Mode

```bash
# Basic transcription
python transcribe.py https://www.youtube.com/watch?v=XXXXX

# With time range
python transcribe.py https://www.youtube.com/watch?v=XXXXX --start 01:30:00 --end 02:00:00

# Custom output file
python transcribe.py https://www.youtube.com/watch?v=XXXXX -o output.txt

# Different model
python transcribe.py https://www.youtube.com/watch?v=XXXXX --model large
```

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output` | Output file path | Auto-generated |
| `-m, --model` | Whisper model (tiny/base/small/medium/large) | medium |
| `-l, --language` | Language code (ru/en/uk) | ru |
| `--start` | Start time (HH:MM:SS) | 0 |
| `--end` | End time (HH:MM:SS) | Full video |
| `--chunk` | Minutes per output chunk | 5 |

## Model Selection

| Model | Size | Speed | Accuracy | VRAM |
|-------|------|-------|----------|------|
| tiny | 39MB | Fastest | Low | ~1GB |
| base | 74MB | Fast | OK | ~1GB |
| small | 244MB | Medium | Good | ~2GB |
| medium | 769MB | Slow | Great | ~5GB |
| large | 1.5GB | Slowest | Best | ~10GB |

**Recommendation:** Use `medium` for Russian speech.

## Output Format

```
============================================================
TRANSCRIPTION
Source: https://www.youtube.com/watch?v=XXXXX
Language: Russian
Segments: 127
============================================================

[00:00:00 - 00:05:00]
Привет всем, сегодня мы поговорим о...

[00:05:00 - 00:10:00]
Как вы видите на экране, первый шаг...

============================================================
END OF TRANSCRIPTION
============================================================
```

## Project Structure

```
youtube-transcriber/
├── gui.py              # GUI application (tkinter)
├── transcribe.py       # Core transcription logic + CLI
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── LICENSE             # MIT License
├── transcriptions/     # Saved transcription files
└── downloads/          # Downloaded audio files
```

## Troubleshooting

### "ffmpeg not found"
Install ffmpeg and add to system PATH:
- Windows: Download from https://ffmpeg.org/download.html
- Extract and add `bin` folder to PATH

### "CUDA out of memory"
Use `--device cpu` or smaller model `--model small`

### Download fails (403 Forbidden)
Make sure Node.js is installed. yt-dlp requires a JavaScript runtime for YouTube extraction.

### Slow transcription
- Use GPU: `--device cuda` (requires NVIDIA GPU)
- Use smaller model: `--model base` or `--model small`

## License

MIT License - see [LICENSE](LICENSE) for details.
