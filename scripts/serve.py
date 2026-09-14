"""Single-container hosting: private API, public UI, readiness and daily SQLite backups."""

import hashlib
import json
import logging
import os
import signal
import sqlite3
import subprocess
import sys
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def healthy(url):
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return response.status == 200
    except OSError:
        return False


def backup(directory):
    dest = directory / "backups"
    dest.mkdir(exist_ok=True)
    today = datetime.now(UTC).strftime("%Y%m%d")
    target = dest / f"history-{today}.sqlite3"
    if target.exists():
        return
    temporary = target.with_suffix(".tmp")
    with (sqlite3.connect(directory / "experiments.sqlite3") as source,
          sqlite3.connect(temporary) as output):
        source.backup(output)
        if output.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("Backup integrity check failed")
    temporary.replace(target)
    for old in sorted(dest.glob("history-*.sqlite3"))[:-7]:
        old.unlink()


def main():
    manifest = json.loads((ROOT / "artifacts/manifest.json").read_text())
    for name, expected in manifest["sha256"].items():
        if hashlib.sha256((ROOT / "artifacts" / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Artifact integrity check failed: {name}")
    port = os.environ.get("PORT", "8080")
    env = os.environ.copy()
    env["QND_API_URL"] = "http://127.0.0.1:8765"
    commands = [
        [sys.executable, "-m", "uvicorn", "qnd.api:app", "--host", "127.0.0.1",
         "--port", "8765", "--no-access-log"],
        [sys.executable, "-m", "streamlit", "run", "dashboard/app.py", "--server.address",
         "0.0.0.0", "--server.port", port, "--server.headless", "true",
         "--server.fileWatcherType", "none", "--server.maxUploadSize", "1",
         "--client.toolbarMode", "minimal"],
    ]
    stopped = False

    def stop(*_):
        nonlocal stopped
        stopped = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    children = []
    try:
        children.append(subprocess.Popen(commands[0], cwd=ROOT, env=env))
        deadline = time.monotonic() + 120
        while not healthy(env["QND_API_URL"] + "/ready"):
            if stopped:
                return
            if children[0].poll() is not None or time.monotonic() > deadline:
                raise RuntimeError("API failed to become ready")
            time.sleep(1)
        children.append(subprocess.Popen(commands[1], cwd=ROOT, env=env))
        started = time.monotonic()
        failures = 0
        last_backup = 0
        while not stopped:
            if any(child.poll() is not None for child in children):
                raise RuntimeError("A service exited; restarting the container")
            ready = healthy(env["QND_API_URL"] + "/ready") and healthy(
                f"http://127.0.0.1:{port}/_stcore/health"
            )
            if ready:
                failures = 0
                if time.monotonic() - last_backup > 3600:
                    backup(Path(os.environ["QND_DATA_DIR"]))
                    last_backup = time.monotonic()
            elif time.monotonic() - started > 120:
                failures += 1
                if failures >= 3:
                    raise RuntimeError("Readiness failed repeatedly; restarting the container")
            time.sleep(5)
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == "__main__":
    main()
