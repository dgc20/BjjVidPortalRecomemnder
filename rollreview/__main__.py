import sys
from pathlib import Path

from .frames import ClipLinkError, close_up, download, first_pass


def main(argv: list[str]) -> int:
    usage = ("usage: python -m rollreview first <video> <out> | "
             "close <video> <t_seconds> <out> | get <url> <dest>")
    try:
        cmd, args = argv[0], argv[1:]
        if cmd == "first" and len(args) == 2:
            paths = first_pass(Path(args[0]), Path(args[1]))
        elif cmd == "close" and len(args) == 3:
            paths = close_up(Path(args[0]), float(args[1]), Path(args[2]))
        elif cmd == "get" and len(args) == 2:
            dest = Path(args[1])
            dest.mkdir(parents=True, exist_ok=True)
            paths = [download(args[0], dest)]
        else:
            raise IndexError
    except IndexError:
        print(usage, file=sys.stderr)
        return 1
    except ClipLinkError as e:
        print(e, file=sys.stderr)
        return 2
    for p in paths:
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
