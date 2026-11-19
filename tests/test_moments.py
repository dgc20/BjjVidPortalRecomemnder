import pytest

from rollreview.frames import ClipLinkError, candidate_moments, download, to_seconds


def test_to_seconds():
    assert to_seconds("1:42") == 102.0
    assert to_seconds("1:02:03") == 3723.0


def test_candidate_moments_basic():
    tl = [["0:14", "standing"], ["0:43", "open guard"], ["1:13", "open guard"], ["1:42", "half guard"]]
    assert candidate_moments(tl) == [
        {"t": 43.0, "from": "standing", "to": "open guard"},
        {"t": 102.0, "from": "open guard", "to": "half guard"}]


def test_not_visible_is_skipped():
    tl = [["0:00", "side control"], ["0:20", "not visible"], ["0:40", "side control"],
          ["1:00", "not visible"], ["1:20", "mount"]]
    assert candidate_moments(tl) == [{"t": 80.0, "from": "side control", "to": "mount"}]


def test_download_bad_link_raises(tmp_path, local_http_server):
    with pytest.raises(ClipLinkError, match="get_clip"):
        download(local_http_server + "/missing.mp4?sig=x", tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_download_odd_filename(tmp_path, local_http_server):
    p = download(local_http_server + "/A%20vs%20B%20%28720p%2C%20h264%29.mp4_r1.mp4?se=1", tmp_path)
    assert p.name == "A vs B (720p, h264).mp4_r1.mp4" and p.stat().st_size > 0


def test_download_truncated_raises_and_cleans_up(tmp_path, local_http_server):
    with pytest.raises(ClipLinkError, match="get_clip"):
        download(local_http_server + "/short.mp4?sig=x", tmp_path)
    assert list(tmp_path.iterdir()) == []
