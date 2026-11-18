import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

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
    try:
        with urllib.request.urlopen(url, timeout=60) as resp, open(part, "wb") as f:
            while chunk := resp.read(1 << 20):
                f.write(chunk)
        part.replace(dest)
    except (urllib.error.URLError, OSError) as e:
        part.unlink(missing_ok=True)
        if isinstance(e, urllib.error.HTTPError) and e.code not in (403, 404):
            raise
        raise ClipLinkError(
            f"Could not download clip ({e}). The link may have expired; "
            "call get_clip again for a fresh watch_url.") from e
    return dest
