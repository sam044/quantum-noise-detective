"""Run from the project Python environment: train, evaluate, and test in an isolated data directory."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
env = os.environ.copy()
env.setdefault("QND_DATA_DIR", str(Path.home() / ".quantum-noise-detective-reproduction"))
env.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="2")
for args in [
    ["-m", "pytest", "tests/test_physics.py", "tests/test_api.py", "-q"],
    ["-m", "qnd.train", "--framework", "torch"],
    ["-m", "qnd.train", "--framework", "tensorflow"],
    ["-m", "qnd.evaluate"],
    ["-m", "pytest", "-q"],
]:
    subprocess.run([sys.executable, *args], cwd=ROOT, env=env, check=True)
print(f"Reproduction complete: {env['QND_DATA_DIR']}")
