#!/usr/bin/env python3
"""Build docs/index.html from the chapter files.

Each book/chapters/NN-*.md becomes a chapter in the site: its text is rendered
to HTML and paired with docs/audio/NN.mp3 (made by scripts/make_audio.py).
Only the book text is shown; the draft banner and review notes are left out.

Run:
    pip install markdown
    python3 scripts/build_site.py
"""

import html
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = ROOT / "book" / "chapters"
AUDIO = ROOT / "docs" / "audio"
OUT = ROOT / "docs" / "index.html"


def book_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = re.split(r"\n---\n\n## Review notes", text)[0]
    lines = [l for l in text.splitlines() if not l.startswith(">")]
    return "\n".join(lines).strip() + "\n"


def chapter_list():
    chapters = []
    for md_path in sorted(CHAPTERS.glob("*.md")):
        num = md_path.name[:2]
        body = book_body(md_path)
        title = re.match(r"# (.+)", body).group(1).strip()
        # The first heading is the chapter title; the body HTML starts after it.
        content = body.split("\n", 1)[1]
        chapters.append({
            "num": num,
            "title": title,
            "html": markdown.markdown(content, extensions=["tables"]),
            "audio": f"audio/{num}.mp3",
            "has_audio": (AUDIO / f"{num}.mp3").exists(),
        })
    return chapters


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Bonobo Code: Women’s Secret to Heaven on Earth</title>
<style>
  :root { --bg:#000; --hot:#FF1493; --neon:#FE53BB; --text:#f5e9f0; --muted:#b58ba3; --panel:#12000a; }
  * { box-sizing: border-box; }
  html, body { margin:0; background:var(--bg); color:var(--text); font:18px/1.7 Helvetica, Arial, sans-serif; }
  .layout { display:grid; grid-template-columns: 280px 1fr; min-height:100vh; }
  nav { border-right:1px solid var(--hot); padding:24px 16px; position:sticky; top:0; height:100vh; overflow:auto; }
  nav h1 { color:var(--neon); font-size:1.4rem; letter-spacing:.06em; margin:0 0 .3em;
           text-shadow:0 0 8px var(--neon), 0 0 24px var(--hot); }
  nav .subtitle { color:var(--text); font-size:1rem; margin:0; }
  .cover { display:block; width:min(240px,70%); margin:0 auto 24px; border-radius:6px;
           box-shadow:0 0 18px rgba(255,20,147,.45); }
  select { background:var(--panel); color:var(--neon); border:1px solid var(--hot); border-radius:8px;
           padding:5px 8px; font:inherit; }
  nav .muted { font-size:.9rem; }
  nav ol { list-style:none; padding:0; margin:1.2em 0 0; }
  nav li { margin:.3em 0; }
  nav button { width:100%; text-align:left; background:none; border:1px solid transparent; color:var(--text);
               padding:8px 10px; border-radius:8px; font:inherit; cursor:pointer; }
  nav button:hover { border-color:var(--hot); }
  nav button[aria-current="true"] { border-color:var(--neon); background:var(--panel); color:var(--neon); }
  main { padding:32px 24px 80px; max-width:760px; width:100%; }
  h2 { color:var(--neon); font-size:clamp(1.6rem,4vw,2.2rem); margin:0 0 .4em;
       text-shadow:0 0 8px var(--neon), 0 0 24px var(--hot); }
  h3 { color:var(--hot); border-bottom:1px solid var(--hot); padding-bottom:.2em; margin-top:2em;
       text-shadow:0 0 10px rgba(255,20,147,.6); }
  .player { position:sticky; top:0; z-index:2; background:var(--bg); border:1px solid var(--hot); border-radius:12px;
            padding:14px 16px; margin:0 0 24px; box-shadow:0 0 14px rgba(255,20,147,.35); }
  .player audio { width:100%; margin:8px 0; }
  .controls { display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
  .controls button { background:var(--panel); color:var(--neon); border:1px solid var(--hot); border-radius:8px;
                     padding:6px 14px; font:inherit; cursor:pointer; }
  .controls button:hover { color:#fff; border-color:var(--neon); }
  .controls label { color:var(--muted); font-size:.95em; }
  .muted { color:var(--muted); }
  .missing { color:var(--muted); font-style:italic; }
  p { margin:1em 0; }
  blockquote { margin:1em 0; padding:.6em 1em; border-left:3px solid var(--neon); background:var(--panel); }
  a { color:var(--neon); } a:hover { color:#fff; text-shadow:0 0 8px var(--neon); }
  ul { padding-left:1.2em; } li { margin:.6em 0; }
  table { border-collapse:collapse; width:100%; margin:1.2em 0; font-size:.95em; }
  th, td { border:1px solid var(--hot); padding:8px 10px; text-align:left; vertical-align:top; }
  th { color:var(--neon); }
  .menu-toggle { display:none; }
  @media (max-width: 800px) {
    .layout { grid-template-columns: 1fr; }
    nav { position:static; height:auto; border-right:none; border-bottom:1px solid var(--hot); padding:16px; }
    nav ol { display:none; }
    nav.open ol { display:block; }
    .menu-toggle { display:block; margin-top:10px; width:100%; background:var(--panel); color:var(--neon);
                   border:1px solid var(--hot); border-radius:8px; padding:8px; font:inherit; }
    main { padding:20px 16px 60px; }
    .player { position:static; }
  }
</style>
</head>
<body>
<div class="layout">
  <nav id="sidebar">
    <h1>THE BONOBO CODE</h1>
    <p class="subtitle">Women’s Secret to Heaven on Earth</p>
    <p class="muted">A book in progress. Pick a chapter and press play.</p>
    <button class="menu-toggle" id="menu-toggle" aria-expanded="false">Chapters</button>
    <ol id="chapter-list">
__NAV__
    </ol>
  </nav>

  <main>
    <img class="cover" src="cover.svg" alt="Cover of The Bonobo Code: Women’s Secret to Heaven on Earth">

    <section class="player" aria-label="Audio player">
      <div class="muted" id="now">Now playing: <span id="now-title"></span></div>
      <audio id="player" controls preload="metadata"></audio>
      <div class="controls">
        <button id="back" type="button" aria-label="Back 15 seconds">&#8630; 15s</button>
        <button id="fwd" type="button" aria-label="Forward 30 seconds">30s &#8631;</button>
        <label>Speed <select id="speed">
          <option value="0.75">0.75&times;</option>
          <option value="1" selected>1&times;</option>
          <option value="1.25">1.25&times;</option>
          <option value="1.5">1.5&times;</option>
        </select></label>
      </div>
      <div class="controls">
        <button id="prev" type="button">&larr; Previous</button>
        <button id="next" type="button">Next &rarr;</button>
        <label><input type="checkbox" id="autoplay" checked> Continue to next chapter</label>
      </div>
      <p class="missing" id="missing" hidden>Audio for this chapter isn’t available yet. The text is below.</p>
    </section>

    <article id="chapter"></article>

    <p class="muted" style="margin-top:3em">Draft. The text is the author’s and has not been fact-checked. The narration is generated with Kokoro, an open-source voice model.</p>
  </main>
</div>

<script>
const chapters = __DATA__;
const player = document.getElementById("player");
const article = document.getElementById("chapter");
const nowTitle = document.getElementById("now-title");
const missing = document.getElementById("missing");
const autoplay = document.getElementById("autoplay");
const sidebar = document.getElementById("sidebar");
const menuToggle = document.getElementById("menu-toggle");
const speed = document.getElementById("speed");
let current = 0;
let lastSave = 0;

// Per-viewer memory of where each chapter was left. Storage can be blocked, so every access is guarded.
const POS_KEY = "bonobo-pos-";
function readPos(num) {
  try { return parseFloat(localStorage.getItem(POS_KEY + num)) || 0; } catch (e) { return 0; }
}
function writePos(num, t) {
  try { localStorage.setItem(POS_KEY + num, String(t)); } catch (e) {}
}

player.addEventListener("loadedmetadata", () => {
  const num = player.dataset.num;
  const saved = readPos(num);
  if (saved > 5 && saved < player.duration - 10) player.currentTime = saved;
  player.playbackRate = parseFloat(speed.value);
});
player.addEventListener("timeupdate", () => {
  if (Date.now() - lastSave > 3000) {
    writePos(player.dataset.num, player.currentTime);
    lastSave = Date.now();
  }
});
player.addEventListener("pause", () => writePos(player.dataset.num, player.currentTime));
speed.addEventListener("change", () => { player.playbackRate = parseFloat(speed.value); });
document.getElementById("back").addEventListener("click", () => {
  player.currentTime = Math.max(0, player.currentTime - 15);
});
document.getElementById("fwd").addEventListener("click", () => {
  player.currentTime = Math.min(player.duration || Infinity, player.currentTime + 30);
});

function indexFromHash() {
  const m = location.hash.match(/^#ch(\\d+)$/);
  if (!m) return 0;
  const i = chapters.findIndex(c => c.num === m[1].padStart(2, "0"));
  return i < 0 ? 0 : i;
}

function show(i, play) {
  if (i < 0 || i >= chapters.length) return;
  current = i;
  const ch = chapters[i];
  article.innerHTML = "<h2>" + ch.title.replace(/</g, "&lt;") + "</h2>" + ch.html;
  nowTitle.textContent = ch.title;
  document.querySelectorAll("#chapter-list button").forEach((b, j) =>
    b.setAttribute("aria-current", j === i ? "true" : "false"));
  missing.hidden = ch.has_audio;
  if (ch.has_audio) {
    player.dataset.num = ch.num;
    player.src = ch.audio;
    player.hidden = false;
    if (play) player.play().catch(() => {});
  } else {
    player.removeAttribute("src");
    player.load();
    player.hidden = true;
  }
  history.replaceState(null, "", "#ch" + ch.num.replace(/^0/, ""));
  window.scrollTo({ top: 0, behavior: "smooth" });
  sidebar.classList.remove("open");
  menuToggle.setAttribute("aria-expanded", "false");
}

document.querySelectorAll("#chapter-list button").forEach((b, j) =>
  b.addEventListener("click", () => show(j, true)));
document.getElementById("prev").addEventListener("click", () => show(current - 1, true));
document.getElementById("next").addEventListener("click", () => show(current + 1, true));
player.addEventListener("ended", () => {
  writePos(player.dataset.num, 0);
  if (autoplay.checked && current < chapters.length - 1) show(current + 1, true);
});
menuToggle.addEventListener("click", () => {
  const open = sidebar.classList.toggle("open");
  menuToggle.setAttribute("aria-expanded", String(open));
});
window.addEventListener("hashchange", () => show(indexFromHash(), false));

show(indexFromHash(), false);
</script>
</body>
</html>
"""


def main() -> None:
    chapters = chapter_list()
    nav = "\n".join(
        f'      <li><button type="button">{html.escape(c["title"])}</button></li>'
        for c in chapters
    )
    data = ",".join(
        "{" + ",".join([
            f'num:"{c["num"]}"',
            f'title:{_js(c["title"])}',
            f'html:{_js(c["html"])}',
            f'audio:"{c["audio"]}"',
            f'has_audio:{"true" if c["has_audio"] else "false"}',
        ]) + "}"
        for c in chapters
    )
    page = PAGE.replace("__NAV__", nav).replace("__DATA__", "[" + data + "]")
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} with {len(chapters)} chapters")


def _js(s: str) -> str:
    """Encode a Python string as a JavaScript string literal."""
    import json
    return json.dumps(s, ensure_ascii=False).replace("</", "<\\/")


if __name__ == "__main__":
    main()
