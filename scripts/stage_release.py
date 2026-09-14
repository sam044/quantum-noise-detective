"""Stage only reviewed serving files, never local databases, credentials or training data."""

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = Path(sys.argv[1]).resolve()
    target.mkdir(parents=True, exist_ok=False)
    for name in ["Dockerfile", ".dockerignore", "requirements-serving.txt",
                 "requirements-lock-linux-serving.txt", ".streamlit/config.toml",
                 "dashboard/app.py", "scripts/serve.py"]:
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, dest)
    for source in (ROOT / "src/qnd").glob("*.py"):
        dest = target / "src/qnd" / source.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    artifacts = ROOT / "artifacts"
    manifest = json.loads((artifacts / "manifest.json").read_text())
    for name, expected in manifest["sha256"].items():
        source = artifacts / name
        if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Artifact changed: {name}")
        dest = target / "artifacts" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    shutil.copy2(artifacts / "manifest.json", target / "artifacts/manifest.json")
    print(f"Staged {sum(p.is_file() for p in target.rglob('*'))} files in {target}")


if __name__ == "__main__":
    main()
