#!/usr/bin/env python3
"""
YouTube Video Transcriber for Russian Speech
=============================================
Downloads a YouTube video, extracts audio, transcribes Russian speech,
and outputs a plain text file with time markers.

Usage:
    python transcribe.py <YouTube_URL> [options]

Requirements:
    pip install faster-whisper yt-dlp
    ffmpeg must be installed and in PATH
"""

import argparse
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

try:
    from faster_whisper import WhisperModel
except ImportError:
    print("Error: faster-whisper not installed. Run: pip install faster-whisper")
    sys.exit(1)

try:
    import yt_dlp
except ImportError:
    print("Error: yt-dlp not installed. Run: pip install yt-dlp")
    sys.exit(1)


class ProgressHook:
    """Progress callback for yt-dlp downloads."""

    def __init__(self):
        self.last_percent = -1

    def __call__(self, d):
        if d["status"] == "downloading":
            percent = d.get("_percent_str", "").strip()
            if percent and percent != self.last_percent:
                self.last_percent = percent
                print(f"\r  Downloading: {percent}", end="", flush=True)
        elif d["status"] == "finished":
            print(f"\r  Download complete.                    ")


def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def download_video(url: str, output_dir: str) -> Optional[str]:
    """
    Download YouTube video and return path to downloaded file.
    
    Args:
        url: YouTube video URL
        output_dir: Directory to save the video
        
    Returns:
        Path to downloaded video file, or None on failure
    """
    print("\n[1/3] Downloading video...")
    
    import subprocess
    import shutil
    
    output_template = os.path.join(output_dir, "video.%(ext)s")
    
    # Find yt-dlp executable
    yt_dlp_path = shutil.which("yt-dlp")
    if not yt_dlp_path:
        # Try python -m yt_dlp
        yt_dlp_path = sys.executable
        cmd = [
            yt_dlp_path, "-m", "yt_dlp",
            "--js-runtimes", "node",
            "-x", "--audio-format", "mp3",
            "--audio-quality", "192",
            "-o", output_template,
            "--no-playlist",
            "--retries", "10",
            "--socket-timeout", "30",
            url
        ]
    else:
        cmd = [
            yt_dlp_path,
            "--js-runtimes", "node",
            "-x", "--audio-format", "mp3",
            "--audio-quality", "192",
            "-o", output_template,
            "--no-playlist",
            "--retries", "10",
            "--socket-timeout", "30",
            url
        ]
    
    print(f"  Running: yt-dlp with node.js runtime")
    
    try:
        # First get video info
        info_cmd = cmd + ["--dump-json", "--skip-download"]
        result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            error_msg = result.stderr.strip()
            if "Private video" in error_msg:
                raise Exception("Video is private or unavailable")
            elif "sign in" in error_msg.lower():
                raise Exception("Video requires sign-in (age-restricted?)")
            elif "Video unavailable" in error_msg:
                raise Exception("Video is unavailable")
            else:
                raise Exception(f"Cannot get video info: {error_msg[:200]}")
        
        import json
        info = json.loads(result.stdout)
        title = info.get("title", "Unknown")
        duration = info.get("duration", 0)
        print(f"  Title: {title}")
        print(f"  Duration: {format_timestamp(duration)}")
        
        # Download
        dl_cmd = [c for c in cmd if c not in ("--dump-json", "--skip-download")]
        result = subprocess.run(dl_cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            error_msg = result.stderr.strip()
            raise Exception(f"Download failed: {error_msg[:200]}")
        
        # Find the downloaded file
        for f in Path(output_dir).iterdir():
            if f.suffix in (".mp3", ".m4a", ".webm", ".opus", ".wav"):
                print(f"  Downloaded: {f.name}")
                return str(f)
        
        print("Error: Downloaded file not found")
        return None
        
    except subprocess.TimeoutExpired:
        raise Exception("Download timed out (10 minutes)")
    except Exception as e:
        raise Exception(f"Download failed: {e}")


def parse_time(time_str: str) -> float:
    """Parse time string (HH:MM:SS or MM:SS or seconds) to seconds."""
    if not time_str:
        return 0.0
    parts = time_str.strip().split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    else:
        return float(parts[0])


def prepare_audio(
    video_path: str,
    output_dir: str,
    start_time: float = 0.0,
    end_time: float = 0.0
) -> Optional[str]:
    """
    Extract and prepare audio for Whisper (16kHz mono WAV).
    
    Args:
        video_path: Path to downloaded video/audio file
        output_dir: Directory for output
        start_time: Start time in seconds (0 = from beginning)
        end_time: End time in seconds (0 = to end)
        
    Returns:
        Path to prepared audio file, or None on failure
    """
    print("\n[2/3] Preparing audio...")
    
    audio_path = os.path.join(output_dir, "audio.wav")
    
    # Build ffmpeg command with time trimming
    ffmpeg_cmd = ["ffmpeg", "-y"]
    
    if start_time > 0:
        ffmpeg_cmd.extend(["-ss", str(start_time)])
    
    ffmpeg_cmd.extend(["-i", video_path])
    
    if end_time > 0:
        ffmpeg_cmd.extend(["-to", str(end_time)])
    
    ffmpeg_cmd.extend([
        "-vn",  # No video
        "-acodec", "pcm_s16le",  # 16-bit PCM
        "-ar", "16000",  # 16kHz
        "-ac", "1",  # Mono
        audio_path
    ])
    
    try:
        import subprocess
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print("  Audio converted to 16kHz mono WAV")
        return audio_path
    except FileNotFoundError:
        print("Error: ffmpeg not found. Install ffmpeg and add to PATH")
        print("  Download: https://ffmpeg.org/download.html")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error during audio conversion: {e.stderr}")
        return None


def transcribe_audio(
    audio_path: str,
    model_size: str = "medium",
    language: str = "ru",
    device: str = "auto",
    compute_type: str = "auto",
    time_offset: float = 0.0,
    progress_callback=None
) -> Optional[list]:
    """
    Transcribe audio using faster-whisper.
    
    Args:
        audio_path: Path to WAV audio file
        model_size: Whisper model size (tiny, base, small, medium, large)
        language: Language code (ru for Russian)
        device: Device to use (auto, cpu, cuda)
        compute_type: Compute type (auto, int8, float16, float32)
        time_offset: Offset to add to timestamps (for trimmed audio)
        progress_callback: Function called with (segments_done, total_estimate)
        
    Returns:
        List of (start_time, end_time, text) tuples, or None on failure
    """
    print(f"\n[3/3] Transcribing with {model_size} model...")
    print("  This may take several minutes for long videos...")
    
    # Auto-detect compute type based on device
    if compute_type == "auto":
        if device == "cuda":
            compute_type = "float16"
        else:
            compute_type = "int8"  # Faster on CPU
    
    # Handle auto language detection
    if language == "auto" or not language:
        language = None
    
    try:
        print(f"  Loading model (device={device}, compute={compute_type})...")
        model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )
        
        print("  Transcribing...")
        start_time = time.time()
        
        segments, info = model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,  # Voice Activity Detection - improves quality
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200
            )
        )
        
        print(f"  Detected language: {info.language} (probability: {info.language_probability:.2f})")
        
        results = []
        segment_count = 0
        
        for segment in segments:
            segment_count += 1
            if segment_count % 10 == 0:
                print(f"  Processed {segment_count} segments...", end="\r")
            
            if progress_callback:
                progress_callback(segment_count, None)
            
            results.append((
                segment.start + time_offset,
                segment.end + time_offset,
                segment.text.strip()
            ))
        
        elapsed = time.time() - start_time
        print(f"  Transcription complete: {segment_count} segments in {elapsed:.1f}s")
        
        return results
        
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None


def format_output(
    segments: list,
    video_url: str,
    chunk_minutes: int = 5
) -> str:
    """
    Format transcription segments into text with time markers.
    
    Args:
        segments: List of (start, end, text) tuples
        video_url: Original video URL
        chunk_minutes: Minutes per output chunk
        
    Returns:
        Formatted text string
    """
    lines = []
    lines.append("=" * 60)
    lines.append("TRANSCRIPTION")
    lines.append(f"Source: {video_url}")
    lines.append(f"Language: Russian")
    lines.append(f"Segments: {len(segments)}")
    lines.append("=" * 60)
    lines.append("")
    
    chunk_seconds = chunk_minutes * 60
    current_chunk_start = 0
    current_chunk_texts = []
    
    for start, end, text in segments:
        # Check if we need to start a new chunk
        if start >= current_chunk_start + chunk_seconds and current_chunk_texts:
            # Write current chunk
            chunk_end = current_chunk_start + chunk_seconds
            chunk_text = " ".join(current_chunk_texts)
            lines.append(f"[{format_timestamp(current_chunk_start)} - {format_timestamp(chunk_end)}]")
            lines.append(chunk_text)
            lines.append("")
            
            current_chunk_start = chunk_end
            current_chunk_texts = []
        
        current_chunk_texts.append(text)
    
    # Write remaining chunk
    if current_chunk_texts:
        last_end = segments[-1][1] if segments else current_chunk_start
        lines.append(f"[{format_timestamp(current_chunk_start)} - {format_timestamp(last_end)}]")
        lines.append(" ".join(current_chunk_texts))
        lines.append("")
    
    lines.append("=" * 60)
    lines.append("END OF TRANSCRIPTION")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe Russian speech from YouTube videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python transcribe.py https://www.youtube.com/watch?v=XXXXX
  python transcribe.py https://youtu.be/XXXXX -o my_transcript.txt
  python transcribe.py https://youtu.be/XXXXX --model large --device cuda
  python transcribe.py https://youtu.be/XXXXX --chunk 10
  python transcribe.py https://youtu.be/XXXXX --start 01:30:00 --end 02:00:00
        """
    )
    
    parser.add_argument(
        "url",
        help="YouTube video URL"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: auto-generated from video title)",
        default=None
    )
    parser.add_argument(
        "-m", "--model",
        choices=["tiny", "base", "small", "medium", "large"],
        default="medium",
        help="Whisper model size (default: medium)"
    )
    parser.add_argument(
        "-l", "--language",
        default="ru",
        help="Language code (default: ru for Russian)"
    )
    parser.add_argument(
        "-d", "--device",
        choices=["auto", "cpu", "cuda"],
        default="auto",
        help="Device to use (default: auto)"
    )
    parser.add_argument(
        "-c", "--compute-type",
        choices=["auto", "int8", "float16", "float32"],
        default="auto",
        help="Compute type (default: auto)"
    )
    parser.add_argument(
        "--chunk",
        type=int,
        default=5,
        help="Minutes per output chunk (default: 5)"
    )
    parser.add_argument(
        "--start",
        type=str,
        default="0",
        help="Start time: HH:MM:SS or MM:SS or seconds (default: 0)"
    )
    parser.add_argument(
        "--end",
        type=str,
        default="0",
        help="End time: HH:MM:SS or MM:SS or seconds (default: 0 = full video)"
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary files (for debugging)"
    )
    
    args = parser.parse_args()
    
    # Validate URL
    if not re.match(r'https?://(www\.)?(youtube\.com|youtu\.be)', args.url):
        print("Error: Invalid YouTube URL")
        print("Expected format: https://www.youtube.com/watch?v=... or https://youtu.be/...")
        sys.exit(1)
    
    print("=" * 60)
    print("YouTube Video Transcriber - Russian Speech")
    print("=" * 60)
    print(f"URL: {args.url}")
    print(f"Model: {args.model}")
    print(f"Language: {args.language}")
    print(f"Device: {args.device}")
    
    start_sec = parse_time(args.start)
    end_sec = parse_time(args.end)
    if start_sec > 0 or end_sec > 0:
        print(f"Time range: {format_timestamp(start_sec)} - {format_timestamp(end_sec) if end_sec > 0 else 'end'}")
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="yt_transcribe_")
    print(f"Working directory: {temp_dir}")
    
    try:
        # Step 1: Download video
        video_path = download_video(args.url, temp_dir)
        if not video_path:
            sys.exit(1)
        
        # Step 2: Prepare audio
        audio_path = prepare_audio(video_path, temp_dir, start_sec, end_sec)
        if not audio_path:
            sys.exit(1)
        
        # Step 3: Transcribe
        segments = transcribe_audio(
            audio_path,
            model_size=args.model,
            language=args.language,
            device=args.device,
            compute_type=args.compute_type,
            time_offset=start_sec
        )
        if not segments:
            sys.exit(1)
        
        # Step 4: Format and save output
        print("\nFormatting output...")
        output_text = format_output(segments, args.url, args.chunk)
        
        # Determine output path
        if args.output:
            output_path = args.output
        else:
            # Save to transcriptions/ folder with video ID as filename
            transcriptions_dir = os.path.join(os.getcwd(), "transcriptions")
            os.makedirs(transcriptions_dir, exist_ok=True)
            
            video_id = re.search(r'(?:v=|youtu\.be/)([^&?]+)', args.url)
            if video_id:
                filename = f"transcript_{video_id.group(1)[:11]}.txt"
            else:
                filename = "transcript.txt"
            output_path = os.path.join(transcriptions_dir, filename)
        
        # Ensure .txt extension
        if not output_path.endswith(".txt"):
            output_path += ".txt"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_text)
        
        print(f"\nTranscription saved to: {output_path}")
        print(f"Total segments: {len(segments)}")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if not args.keep_temp:
            print("Cleaning up temporary files...")
            shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            print(f"Temporary files kept at: {temp_dir}")


if __name__ == "__main__":
    main()
