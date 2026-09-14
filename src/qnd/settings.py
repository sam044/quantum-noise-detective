"""All generated state lives outside the source checkout by default."""

import os
from pathlib import Path


def data_dir() -> Path:
    path = Path(os.environ.get("QND_DATA_DIR", Path.home() / ".quantum-noise-detective"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def model_dir() -> Path:
    path = Path(os.environ.get("QND_MODELS_DIR", data_dir() / "models"))
    path.mkdir(parents=True, exist_ok=True)
    return path
