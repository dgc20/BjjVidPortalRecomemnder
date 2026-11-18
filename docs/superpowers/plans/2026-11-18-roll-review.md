# Roll Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A `review-roll` Claude Code skill that pulls a roll from bjj-silver, extracts frames in two passes, and writes a per-roll review plus a running habits log of lost positional battles and why.

**Architecture:** A small Python helper (`rollreview/frames.py`) does the mechanical work: downloading a clip, finding candidate moments in the timeline, and extracting frames with a bundled ffmpeg. The skill file (`SKILL.md`) tells Claude the review procedure: which bjj-silver tools to call, when to run the helper, how to judge the frames, and how to write the review and habits files. The judging itself is Claude reading frames, so it is not code.

**Tech Stack:** Python 3.15, `imageio-ffmpeg` (ships its own ffmpeg binary, so no system install), `pytest`, the bjj-silver MCP tools (`get_clip`, `search_clips`).

**Spec:** `roll-review-design.md`

## Global Constraints

- You name which grappler you are on every request. Nothing about how you look is stored.
- Signed `watch_url` links expire within hours, so every review fetches a fresh one with `get_clip`. Links are never cached.
- Frames go to a temp folder and are deleted after each review. Only the markdown files are kept.
- First pass: 1 fps. Close-up pass: 8 fps over the 5 s before each moment.
- Every "why" carries a confidence rating (high/medium/low). When the cause isn't visible, the review says "can't tell from the footage".
- Kept files: `reviews/<clip>.md`, `habits.md`, `bjj-reference.md`.

## Review Focus

1. **Moment near the start of the clip (t < 5 s):** the close-up window is clamped to 0 and doesn't crash. The test goes in Task 2.
2. **Clip name with spaces, parentheses or commas** (e.g. `Daniel Cohen vs ... (720p, h264).mp4_r1.mp4`): download and output paths still work. The test goes in Task 1.
3. **Timeline with "not visible" between two positions:** it isn't reported as two position changes. A→not visible→A is no change, and A→not visible→B counts as one change. The test goes in Task 1.
4. **Expired or broken `watch_url`:** fails with a clear message telling the skill to call `get_clip` again. It never leaves a half-written file. The test goes in Task 1.
5. **Very long clip (> 10 min):** the first pass caps at 600 frames by lowering the fps, and says so. The test goes in Task 2.

---

### Task 1: Clip download and timeline moments

**Files:**
- Create: `rollreview/__init__.py`, `rollreview/frames.py`, `requirements.txt` (`imageio-ffmpeg`, `pytest`)
- Test: `tests/test_moments.py`

**Interfaces:**
- Produces: `to_seconds(stamp: str) -> float` (handles `"m:ss"` and `"h:mm:ss"`); `candidate_moments(timeline: list[list[str]]) -> list[dict]`, each dict `{"t": float, "from": str, "to": str}`; `download(url: str, dest_dir: Path) -> Path`, which raises `ClipLinkError` on HTTP 403/404 or a network error.

- [ ] **Step 1: Write failing tests**

```python
def test_to_seconds():
    assert to_seconds("1:42") == 102.0
    assert to_seconds("1:02:03") == 3723.0

def test_candidate_moments_basic():
    tl = [["0:14","standing"],["0:43","open guard"],["1:13","open guard"],["1:42","half guard"]]
    assert candidate_moments(tl) == [
        {"t": 43.0, "from": "standing", "to": "open guard"},
        {"t": 102.0, "from": "open guard", "to": "half guard"}]

def test_not_visible_is_skipped():
    tl = [["0:00","side control"],["0:20","not visible"],["0:40","side control"],["1:00","not visible"],["1:20","mount"]]
    assert candidate_moments(tl) == [{"t": 80.0, "from": "side control", "to": "mount"}]

def test_download_bad_link_raises(tmp_path):
    with pytest.raises(ClipLinkError, match="get_clip"):
        download("https://bjjstoragecool.blob.core.windows.net/bjj-clips/nope.mp4?sig=x", tmp_path)
    assert list(tmp_path.iterdir()) == []

def test_download_odd_filename(tmp_path, local_http_server):
    # local_http_server fixture serves tests/data/tiny.mp4 under the name "A vs B (720p, h264).mp4_r1.mp4"
    p = download(local_http_server + "/A%20vs%20B%20%28720p%2C%20h264%29.mp4_r1.mp4?se=1", tmp_path)
    assert p.name == "A vs B (720p, h264).mp4_r1.mp4" and p.stat().st_size > 0
```

- [ ] **Step 2: Run** `python -m pytest tests/test_moments.py -v`. Expected: FAIL (import error).
- [ ] **Step 3: Implement** in `rollreview/frames.py`. `download` uses `urllib.request`, takes the file name from the URL-decoded path (query dropped), writes to `<name>.part`, and renames only on success. `tests/conftest.py` provides `local_http_server` (a `http.server` thread) and makes `tests/data/tiny.mp4` with imageio-ffmpeg's `testsrc` (10 s, 320x240).
- [ ] **Step 4: Run** the tests. Expected: 5 passed.
- [ ] **Step 5: Commit** `feat: clip download and timeline moments`

### Task 2: Frame extraction (two passes) and CLI

**Files:**
- Modify: `rollreview/frames.py`
- Create: `rollreview/__main__.py`
- Test: `tests/test_extract.py`

**Interfaces:**
- Consumes: `to_seconds`, `candidate_moments`, `download` from Task 1.
- Produces:
  - `first_pass(video: Path, out_dir: Path, fps: float = 1.0, max_frames: int = 600) -> list[Path]`. Frames are named `f_<mm>m<ss>s.jpg`. If `duration * fps > max_frames`, it lowers fps to `max_frames / duration` and prints a note.
  - `close_up(video: Path, t: float, out_dir: Path, window: float = 5.0, fps: float = 8.0) -> list[Path]`. It covers `[max(0, t-window), t+1]`, and frames are named `c_<t>_<offset>.jpg`.
  - `duration(video: Path) -> float`.
  - CLI: `python -m rollreview first <video> <out>`, `python -m rollreview close <video> <t_seconds> <out>`, `python -m rollreview get <url> <dest>`. Each prints one output path per line.

- [ ] **Step 1: Write failing tests**

```python
def test_first_pass_count(tiny_video, tmp_path):
    frames = first_pass(tiny_video, tmp_path)          # 10 s clip
    assert 9 <= len(frames) <= 11 and frames[0].name.startswith("f_")

def test_first_pass_caps_long_clip(tiny_video, tmp_path, capsys):
    frames = first_pass(tiny_video, tmp_path, fps=100, max_frames=50)
    assert len(frames) <= 51 and "lowered" in capsys.readouterr().out

def test_close_up_window(tiny_video, tmp_path):
    frames = close_up(tiny_video, 6.0, tmp_path)        # 1..7 s at 8 fps
    assert 45 <= len(frames) <= 50

def test_close_up_clamps_at_start(tiny_video, tmp_path):
    frames = close_up(tiny_video, 2.0, tmp_path)        # 0..3 s
    assert 22 <= len(frames) <= 26
```

- [ ] **Step 2: Run** `python -m pytest tests/test_extract.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** with `imageio_ffmpeg.get_ffmpeg_exe()` and `subprocess.run` (`-ss`/`-to` before `-i`, `-vf fps=N,scale=960:-2`, `-q:v 3`). `duration` parses `Duration:` from ffmpeg's stderr.
- [ ] **Step 4: Run** the full suite `python -m pytest -v`. Expected: all pass.
- [ ] **Step 5: Commit** `feat: two-pass frame extraction and CLI`

### Task 3: The review-roll skill and kept files

**Files:**
- Create: `~/.claude/skills/review-roll/SKILL.md` (user scope, so it works in every session); `bjj-reference.md`, `habits.md`, `reviews/.gitkeep` in the project folder

**Interfaces:**
- Consumes: the CLI from Task 2; the bjj-silver tools `get_clip(clip)`, `search_clips(position=, type="rolling", limit=)`.

- [ ] **Step 1: Write `SKILL.md`.** Its frontmatter `description` triggers on "review my roll / review <clip>". The body is the procedure:
  1. Require "which one are you". If it's missing, ask, and don't proceed.
  2. `get_clip` → `python -m rollreview get` into a temp folder.
  3. Read `bjj-reference.md`.
  4. `first` pass. Look at the frames together with `candidate_moments` from the timeline, and decide which changes went against the user.
  5. For each loss: `close` pass, then the "what broke first" judgment with a confidence rating.
  6. `search_clips(position=<lost position>)` for up to 3 comparison clips, using their summaries and timelines only. Don't download those clips unless the user asks.
  7. Write `reviews/<clip>.md`. For each loss: `timestamp`, `from → to`, `what happened`, `why`, `confidence`, `portal_url`.
  8. Update `habits.md`. Match an existing row when the lost position and the cause are the same, otherwise add a row (`habit | count | clips | latest example`).
  9. Delete the temp folder.
  10. When the user corrects a term or call, append it to `bjj-reference.md`.
- [ ] **Step 2: Seed `bjj-reference.md`** with bjj-silver's position vocabulary (open/closed/half/butterfly guard, side control, mount, back control, turtle, standing, scramble, leg entanglement) and the visual cue for each one. Seed `habits.md` with an empty table header.
- [ ] **Step 3: Verify end to end** on a real short clip: "review IMG_1460.MOV_r1.mp4", telling it which grappler is you. Expected: `reviews/IMG_1460.MOV_r1.mp4.md` exists with ≥1 loss entry and a confidence on each one, `habits.md` has ≥1 row, and the temp frames folder is gone.
- [ ] **Step 4: Commit** `feat: review-roll skill and seed files`
