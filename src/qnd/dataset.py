"""Reproducible, independent latent configurations in each split."""

import hashlib
import json
import time
from pathlib import Path

import numpy as np

from qnd.physics import PROTOCOL, SHOTS, TIMES, probabilities


def generate_split(n, seed, shots=SHOTS, t1_range=(10, 100), phi_range=(10, 200)):
    rng = np.random.default_rng(seed)
    t1 = np.exp(rng.uniform(*np.log(t1_range), n))
    phi = np.exp(rng.uniform(*np.log(phi_range), n))
    rates = np.column_stack([1 / t1, 1 / phi])
    counts = rng.binomial(shots, probabilities(rates[:, 0], rates[:, 1])).astype(np.int16)
    return counts, rates


def make_dataset(path: Path, n_train=6000, seed=20260911):
    start = time.perf_counter()
    payload = {}
    sizes = {"train": n_train, "validation": 800, "calibration": 800, "test": 800}
    for i, (split, n) in enumerate(sizes.items()):
        counts, rates = generate_split(n, seed + i * 1009)
        payload[f"{split}_counts"] = counts
        payload[f"{split}_rates"] = rates
    np.savez_compressed(path, **payload)
    manifest = {
        "protocol": PROTOCOL,
        "seed": seed,
        "sizes": sizes,
        "shots": SHOTS,
        "times_us": TIMES.tolist(),
        "distribution": "independent log-uniform T1 and Tphi",
        "t1_range_us": [10, 100],
        "tphi_range_us": [10, 200],
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "generation_seconds": time.perf_counter() - start,
        "uncompressed_bytes": sum(x.nbytes for x in payload.values()),
    }
    path.with_suffix(".json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
