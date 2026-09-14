"""Local lab supervisor: detached startup, singleton, and child crash recovery."""

import logging
import os
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from logging.handlers import RotatingFileHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG_DIR = Path.home() / ".quantum-noise-detective" / "logs"
URL = "http://127.0.0.1:8501/"
LOGGER = logging.getLogger(__name__)


def healthy(url):
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return response.status == 200
    except OSError:
        return False


def ready():
    return healthy(URL + "_stcore/health") and healthy("http://127.0.0.1:8765/health")


def wait_ready():
    for _ in range(90):
        if ready():
            return
        time.sleep(1)
    raise RuntimeError(f"Lab did not start. See {LOG_DIR}")


def main():
    if "--background" in sys.argv:
        if not ready():
            executable = Path(sys.executable)
            if os.name == "nt":
                executable = executable.with_name("pythonw.exe")
            subprocess.Popen(
                [str(executable), str(ROOT / "launch.py"), "--no-browser"],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=(subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
                if os.name == "nt"
                else 0,
                start_new_session=os.name != "nt",
            )
        wait_ready()
        webbrowser.open(URL)
        return
    lock = socket.socket()
    if os.name == "nt":
        lock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    try:
        lock.bind(("127.0.0.1", 8766))
        lock.listen(1)
    except OSError:
        lock.close()
        wait_ready()
        if "--no-browser" not in sys.argv:
            webbrowser.open(URL)
        return
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            RotatingFileHandler(LOG_DIR / "supervisor.log", maxBytes=2_000_000, backupCount=2)
        ],
    )
    env = os.environ.copy()
    env.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="2")
    commands = {
        "api": [
            sys.executable,
            "-m",
            "uvicorn",
            "qnd.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
        ],
        "dashboard": [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "dashboard/app.py",
            "--server.port",
            "8501",
        ],
    }
    children, streams, started = {}, {}, {}
    failures = dict.fromkeys(commands, 0)
    retry_at = dict.fromkeys(commands, 0.0)
    opened = "--no-browser" in sys.argv
    LOGGER.info("Supervisor starting pid=%s", os.getpid())
    try:
        while True:
            for name, command in commands.items():
                process = children.get(name)
                if process is not None and process.poll() is not None:
                    failures[name] = (
                        failures[name] + 1 if time.monotonic() - started[name] < 60 else 1
                    )
                    delay = min(60, 2 ** min(failures[name], 6))
                    LOGGER.warning(
                        "%s exited code=%s; restarting in %ss", name, process.returncode, delay
                    )
                    streams.pop(name).close()
                    del children[name]
                    retry_at[name] = time.monotonic() + delay
                if name not in children and time.monotonic() >= retry_at[name]:
                    # A restarted supervisor can reuse services left alive by its predecessor.
                    health_url = (
                        "http://127.0.0.1:8765/health" if name == "api" else URL + "_stcore/health"
                    )
                    if healthy(health_url):
                        continue
                    path = LOG_DIR / f"{name}.log"
                    if path.exists() and path.stat().st_size > 5_000_000:
                        path.replace(LOG_DIR / f"{name}.previous.log")
                    streams[name] = path.open("ab", buffering=0)
                    children[name] = subprocess.Popen(
                        command,
                        cwd=ROOT,
                        env=env,
                        stdin=subprocess.DEVNULL,
                        stdout=streams[name],
                        stderr=subprocess.STDOUT,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                    )
                    started[name] = time.monotonic()
                    LOGGER.info("Started %s pid=%s", name, children[name].pid)
            if not opened and ready():
                webbrowser.open(URL)
                opened = True
            time.sleep(2)
    except KeyboardInterrupt:
        LOGGER.info("Stopped by keyboard interrupt")
    except Exception:
        LOGGER.exception("Supervisor failed")
        raise
    finally:
        for process in children.values():
            if process.poll() is None:
                process.terminate()
        for process in children.values():
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        for stream in streams.values():
            stream.close()
        lock.close()


if __name__ == "__main__":
    main()
