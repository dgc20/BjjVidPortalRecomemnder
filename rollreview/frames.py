import http.client
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import imageio_ffmpeg

NOT_VISIBLE = "not visible"


class ClipLinkError(Exception):
    pass


def to_seconds(stamp: str) -> float:
    total = 0.0
    for part in stamp.split(":"):
        total = total * 60 + float(part)
    return total


def candidate_moments(timeline: list[list[str]]) -> list[dict]:
    """Position changes between consecutive visible timeline entries."""
    moments = []
    prev = None
    for stamp, position in timeline:
        if position == NOT_VISIBLE:
            continue
        if prev is not None and position != prev:
            moments.append({"t": to_seconds(stamp), "from": prev, "to": position})
        prev = position
    return moments


def download(url: str, dest_dir: Path) -> Path:
    name = Path(urllib.parse.unquote(urllib.parse.urlsplit(url).path)).name
    dest = Path(dest_dir) / name
    part = dest.with_name(dest.name + ".part")
    done = False
    try:
        with urllib.request.urlopen(url, timeout=60) as resp, open(part, "wb") as f:
            expected = resp.headers.get("Content-Length")
            written = 0
            while chunk := resp.read(1 << 20):
                f.write(chunk)
                written += len(chunk)
        if expected is not None and written != int(expected):
            raise ClipLinkError(
                f"Download was cut short ({written} of {expected} bytes). "
                "Call get_clip again for a fresh watch_url.")
        part.replace(dest)
        done = True
    except (urllib.error.URLError, OSError, http.client.HTTPException) as e:
        if isinstance(e, urllib.error.HTTPError) and e.code not in (403, 404):
            raise
        raise ClipLinkError(
            f"Could not download clip ({e}). The link may have expired; "
            "call get_clip again for a fresh watch_url.") from e
    finally:
        if not done:
            part.unlink(missing_ok=True)
    return dest


def _ffmpeg() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def duration(video: Path) -> float:
    r = subprocess.run([_ffmpeg(), "-i", str(video)], capture_output=True, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", r.stderr)
    if not m:
        raise ValueError(f"Could not read duration of {video}")
    h, mi, sec = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(sec)


def _extract(video: Path, pattern: str, fps: float, start: float = 0.0,
             length: float | None = None) -> None:
    cmd = [_ffmpeg(), "-y", "-v", "error", "-ss", f"{start:.3f}"]
    if length is not None:
        cmd += ["-t", f"{length:.3f}"]
    cmd += ["-i", str(video), "-vf", f"fps={fps},scale=960:-2", "-q:v", "3", pattern]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {r.stderr.strip()}")


def first_pass(video: Path, out_dir: Path, fps: float = 1.0,
               max_frames: int = 600) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dur = duration(video)
    if dur * fps > max_frames:
        fps = max_frames / dur
        print(f"Note: fps lowered to {fps:.3f} to stay within {max_frames} frames.")
    _extract(video, str(out_dir / "tmp_%04d.jpg"), fps)
    frames = []
    for i, tmp in enumerate(sorted(out_dir.glob("tmp_*.jpg"))):
        secs = int(i / fps)
        dest = out_dir / f"f_{i:04d}_{secs // 60:02d}m{secs % 60:02d}s.jpg"
        tmp.replace(dest)
        frames.append(dest)
    return frames


def close_up(video: Path, t: float, out_dir: Path, window: float = 5.0,
             fps: float = 8.0) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    start = max(0.0, t - window)
    _extract(video, str(out_dir / "tmp_%03d.jpg"), fps, start, t + 1 - start)
    frames = []
    for i, tmp in enumerate(sorted(out_dir.glob("tmp_*.jpg"))):
        dest = out_dir / f"c_{t:09.1f}_{i:03d}.jpg"
        tmp.replace(dest)
        frames.append(dest)
    return frames
