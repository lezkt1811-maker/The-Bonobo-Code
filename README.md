# The Bonobo Code

A book in progress. The live site at the project's GitHub Pages address has the full text of each chapter, with a narrated audio version of each one.

- [`book/chapters/`](book/chapters/): the manuscript, one file per chapter. This is the source for the site and the audio.
- [`book/00-book-plan.md`](book/00-book-plan.md): the outline the book follows.
- [`docs/`](docs/): the published site (`index.html`) and the chapter audio (`audio/`).
- [`scripts/`](scripts/): the tools that build the site and the audio.
- [`notes/`](notes/): earlier research notes, kept for reference and possible later use. These are not part of the book.

## Rebuilding the site and the audio

When a chapter changes, rebuild its audio and the site, then commit the result.

```bash
# one-time setup
python3 -m venv .venv && . .venv/bin/activate
pip install kokoro-onnx soundfile markdown
# ffmpeg must also be installed

# rebuild audio for all chapters (or pass a chapter number, e.g. 03)
python3 scripts/make_audio.py

# rebuild the site from the chapter files
python3 scripts/build_site.py
```

The narration uses [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (Apache 2.0) through [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx). The model downloads to `~/.cache/bonobo-tts/` on first run. Audio is generated from the book text only; the draft banner and any "Review notes" section are skipped.
