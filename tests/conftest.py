import subprocess
import threading
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import imageio_ffmpeg
import pytest

DATA = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def tiny_video():
    path = DATA / "tiny.mp4"
    if not path.exists():
        DATA.mkdir(exist_ok=True)
        subprocess.run(
            [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-f", "lavfi", "-i",
             "testsrc=duration=10:size=320x240:rate=30", "-pix_fmt", "yuv420p", str(path)],
            check=True, capture_output=True)
    return path


class _Handler(BaseHTTPRequestHandler):
    video = None

    def do_GET(self):
        name = self.path.split("?")[0]
        if not name.endswith(".mp4") or name.endswith("/missing.mp4"):
            self.send_error(404)
            return
        data = self.video.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture
def local_http_server(tiny_video):
    handler = type("Handler", (_Handler,), {"video": tiny_video})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
