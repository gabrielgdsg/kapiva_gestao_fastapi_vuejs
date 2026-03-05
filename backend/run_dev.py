#!/usr/bin/env python3
"""
Dev runner: watch .env and Python files; restart uvicorn on any change.
This way .env changes take effect without manually restarting the container.
"""
import os
import subprocess
import sys
from pathlib import Path

# Load .env into environment (dotenv format: KEY=value)
def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip()
                if k:
                    # Remove surrounding quotes
                    if len(v) >= 2 and v[0] == v[-1] and v[0] in '"\'':
                        v = v[1:-1]
                    os.environ[k] = v


def main() -> int:
    app_dir = Path(__file__).resolve().parent
    os.chdir(app_dir)
    env_file = app_dir / ".env"
    load_dotenv(env_file)

    # Watch .env and all Python under app, gmail, extraction
    watch_dirs = [app_dir / "app", app_dir / "gmail", app_dir / "extraction"]
    watch_dirs = [d for d in watch_dirs if d.exists()]
    watch_files = [env_file] if env_file.exists() else []
    # Build list of paths for watchfiles
    from watchfiles import watch

    uvicorn_cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
    ]
    proc = None
    try:
        load_dotenv(env_file)
        proc = subprocess.Popen(uvicorn_cmd, cwd=app_dir, env=os.environ)
        for _ in watch(*watch_dirs, *watch_files, raise_interrupt=False):
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            load_dotenv(env_file)
            proc = subprocess.Popen(uvicorn_cmd, cwd=app_dir, env=os.environ)
    except KeyboardInterrupt:
        pass
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
