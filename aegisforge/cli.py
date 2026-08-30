from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path

import uvicorn

from . import __version__
from . import models as _models  # noqa: F401
from .api import create_app
from .config import load_settings
from .db import Base, make_engine, reset_legacy_alpha_schema
from .errors import EXIT_CODES, AegisForgeError, ErrorCode

OK = 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aegisforge")
    parser.add_argument("--config")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("version")
    sub.add_parser("init")
    serve = sub.add_parser("serve")
    serve.add_argument("--host")
    serve.add_argument("--port", type=int)
    serve.add_argument("--offline", action="store_true")
    serve.add_argument("--detach", action="store_true")
    sub.add_parser("stop")
    sub.add_parser("worker")
    for name in ["doctor", "plugins", "integrations", "target", "scan", "findings", "report", "frameworks"]:
        p = sub.add_parser(name)
        p.add_argument("args", nargs="*")
    args = parser.parse_args(argv)
    try:
        return _run(args)
    except AegisForgeError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_CODES[exc.code]
    except Exception as exc:  # noqa: BLE001 - top-level CLI maps unexpected failures to exit code 1.
        print(str(exc), file=sys.stderr)
        return EXIT_CODES[ErrorCode.internal_error]


def _run(args: argparse.Namespace) -> int:
    settings = load_settings(
        Path(args.config) if args.config else None,
        {
            k: v
            for k, v in {
                "host": getattr(args, "host", None),
                "port": getattr(args, "port", None),
                "offline": getattr(args, "offline", None),
            }.items()
            if v not in {None, False}
        },
    )
    if args.cmd == "version":
        print(__version__)
    elif args.cmd == "init":
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        engine = make_engine(settings.database_url)
        reset_legacy_alpha_schema(engine, Base)
        Base.metadata.create_all(engine)
        print(f"initialized {settings.data_dir}")
    elif args.cmd == "serve":
        if args.detach:
            return _detach(args)
        uvicorn.run(create_app(settings), host=settings.host, port=settings.port)
    elif args.cmd == "stop":
        return _stop(settings.data_dir)
    elif args.cmd == "worker":
        print("worker idle")
    else:
        print(f"{args.cmd} command skeleton")
    return OK


def _detach(args: argparse.Namespace) -> int:
    # Detached mode is the only mode managed by `aegisforge stop`; foreground uses Ctrl+C.
    cmd = [
        sys.executable,
        "-m",
        "aegisforge.cli",
        *(["--config", args.config] if args.config else []),
        "serve",
    ]
    if args.host:
        cmd += ["--host", args.host]
    if args.port:
        cmd += ["--port", str(args.port)]
    if args.offline:
        cmd += ["--offline"]
    settings = load_settings(Path(args.config) if args.config else None)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    log = (settings.data_dir / "serve.log").open("a", encoding="utf-8")
    proc = subprocess.Popen(cmd, stdout=log, stderr=log, start_new_session=os.name != "nt")
    (settings.data_dir / "serve.pid").write_text(str(proc.pid), encoding="utf-8")
    print(f"started {proc.pid}")
    return OK


def _stop(data_dir: Path) -> int:
    # Keep stop boring: remove only the pidfile we own after signaling that process.
    pid_file = data_dir / "serve.pid"
    if not pid_file.exists():
        print("no detached server")
        return OK
    pid = int(pid_file.read_text(encoding="utf-8"))
    os.kill(pid, signal.SIGTERM)
    pid_file.unlink()
    print(f"stopped {pid}")
    return OK


if __name__ == "__main__":
    raise SystemExit(main())
