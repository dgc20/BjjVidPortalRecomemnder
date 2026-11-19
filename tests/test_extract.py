import subprocess
import sys

from rollreview.frames import close_up, duration, first_pass


def test_duration(tiny_video):
    assert 9.9 <= duration(tiny_video) <= 10.1


def test_first_pass_count(tiny_video, tmp_path):
    frames = first_pass(tiny_video, tmp_path)
    assert 9 <= len(frames) <= 11 and frames[0].name.startswith("f_")
    assert [f.name for f in frames] == sorted(f.name for f in frames)
    assert all(f.exists() for f in frames)


def test_first_pass_caps_long_clip(tiny_video, tmp_path, capsys):
    frames = first_pass(tiny_video, tmp_path, fps=100, max_frames=50)
    assert len(frames) <= 51 and "lowered" in capsys.readouterr().err


def test_close_up_window(tiny_video, tmp_path):
    frames = close_up(tiny_video, 6.0, tmp_path)
    assert 45 <= len(frames) <= 50
    assert frames[0].name.startswith("c_")


def test_close_up_clamps_at_start(tiny_video, tmp_path):
    frames = close_up(tiny_video, 2.0, tmp_path)
    assert 22 <= len(frames) <= 26


def test_cli_first_and_close(tiny_video, tmp_path):
    r = subprocess.run([sys.executable, "-m", "rollreview", "first", str(tiny_video),
                        str(tmp_path / "a")], capture_output=True, text=True)
    assert r.returncode == 0 and len(r.stdout.split("\n")) >= 10
    r = subprocess.run([sys.executable, "-m", "rollreview", "close", str(tiny_video), "2",
                        str(tmp_path / "b")], capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip().endswith(".jpg")


def test_cli_get_error_exit_code(tmp_path):
    r = subprocess.run([sys.executable, "-m", "rollreview", "get",
                        "http://127.0.0.1:1/x.mp4", str(tmp_path)],
                       capture_output=True, text=True)
    assert r.returncode == 2 and "Could not download" in r.stderr
