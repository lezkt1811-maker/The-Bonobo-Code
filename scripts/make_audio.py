#!/usr/bin/env python3
"""Generate narrated MP3s for each book chapter.

Reads book/chapters/NN-*.md, keeps only the book text (everything above the
"Review notes" section), synthesizes it with Kokoro-82M (Apache 2.0, runs on a
CPU), and writes docs/audio/NN.mp3 for the site to play.

Setup (once):
    pip install kokoro-onnx soundfile
    ffmpeg must be on PATH.

Run:
    python3 scripts/make_audio.py            # all chapters
    python3 scripts/make_audio.py 03         # one chapter

Model files are downloaded on first run to ~/.cache/bonobo-tts/.
"""

import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = ROOT / "book" / "chapters"
OUT = ROOT / "docs" / "audio"
CACHE = Path.home() / ".cache" / "bonobo-tts"

MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

VOICE = "af_heart"  # warm, natural American female voice in Kokoro
SPEED = 0.93        # slightly slower than default for narration
SAMPLE_RATE = 24000
MAX_CHARS = 300     # sentences are grouped up to this length per synthesis call

PAUSE_HEADING = 1.0
PAUSE_BLOCK = 0.6
PAUSE_LIST_ITEM = 0.4


def fetch(url: str, dest: Path) -> Path:
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading {dest.name} ...")
        urllib.request.urlretrieve(url, dest)
    return dest


def load_model() -> Kokoro:
    model = fetch(MODEL_URL, CACHE / "kokoro-v1.0.onnx")
    voices = fetch(VOICES_URL, CACHE / "voices-v1.0.bin")
    return Kokoro(str(model), str(voices))


def book_text(path: Path) -> str:
    """Return the chapter body, without the draft banner or review notes."""
    text = path.read_text(encoding="utf-8")
    text = re.split(r"\n---\n\n## Review notes", text)[0]
    lines = [l for l in text.splitlines() if not l.startswith(">")]
    return "\n".join(lines)


def clean_inline(s: str) -> str:
    s = s.replace("—", ", ").replace("–", "-")
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"\*(.+?)\*", r"\1", s)
    s = s.replace("`", "")
    return re.sub(r"\s+", " ", s).strip()


def segments(md: str):
    """Yield (kind, text) where kind is 'speech' or 'pause' (seconds as float)."""
    for block in re.split(r"\n\s*\n", md):
        block = block.strip()
        if not block:
            continue
        if block.startswith("#"):
            title = clean_inline(block.lstrip("#").strip())
            yield ("speech", title)
            yield ("pause", PAUSE_HEADING)
        elif block.startswith("|"):
            rows = [r for r in block.splitlines() if not re.match(r"^\|\s*-", r)]
            for row in rows:
                cells = [clean_inline(c) for c in row.strip().strip("|").split("|")]
                cells = [c for c in cells if c]
                if cells:
                    yield ("speech", ". ".join(cells) + ".")
                    yield ("pause", PAUSE_LIST_ITEM)
            yield ("pause", PAUSE_BLOCK)
        elif re.match(r"^\s*[*-] ", block):
            for item in re.split(r"\n(?=\s*[*-] )", block):
                item = re.sub(r"^\s*[*-] ", "", item)
                yield ("speech", clean_inline(item))
                yield ("pause", PAUSE_LIST_ITEM)
            yield ("pause", PAUSE_BLOCK)
        elif block.startswith("---"):
            continue
        else:
            yield ("speech", clean_inline(block.replace("\n", " ")))
            yield ("pause", PAUSE_BLOCK)


def sentence_chunks(text: str):
    """Group sentences into chunks no longer than MAX_CHARS."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunk = ""
    for s in sentences:
        if chunk and len(chunk) + len(s) + 1 > MAX_CHARS:
            yield chunk
            chunk = s
        else:
            chunk = f"{chunk} {s}".strip()
    if chunk:
        yield chunk


def synthesize(kokoro: Kokoro, text: str) -> np.ndarray:
    parts = []
    for chunk in sentence_chunks(text):
        samples, _ = kokoro.create(chunk, voice=VOICE, speed=SPEED, lang="en-us")
        parts.append(samples)
    return np.concatenate(parts) if parts else np.zeros(0, dtype=np.float32)


def render(kokoro: Kokoro, md_path: Path, out_path: Path) -> None:
    pieces = []
    for kind, value in segments(book_text(md_path)):
        if kind == "pause":
            pieces.append(np.zeros(int(SAMPLE_RATE * value), dtype=np.float32))
        else:
            pieces.append(synthesize(kokoro, value))
            pieces.append(np.zeros(int(SAMPLE_RATE * 0.15), dtype=np.float32))

    audio = np.concatenate(pieces)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "chapter.wav"
        sf.write(wav, audio, SAMPLE_RATE)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
             "-codec:a", "libmp3lame", "-b:a", "64k", "-ac", "1", str(out_path)],
            check=True,
        )
    minutes = len(audio) / SAMPLE_RATE / 60
    print(f"wrote {out_path.relative_to(ROOT)} ({minutes:.1f} min)")


def main() -> None:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    kokoro = load_model()
    for md_path in sorted(CHAPTERS.glob("*.md")):
        num = md_path.name[:2]
        if only and num != only.zfill(2):
            continue
        render(kokoro, md_path, OUT / f"{num}.mp3")


if __name__ == "__main__":
    main()
