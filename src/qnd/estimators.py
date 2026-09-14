"""Count-only inference. Ground truth is never an estimator input."""

import json
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.optimize import least_squares, minimize

from qnd.physics import SHOTS, TIMES, probabilities


def validate_counts(counts, shots):
    counts = np.asarray(counts)
    if counts.shape != (2, 64) or not np.all(np.isfinite(counts)):
        raise ValueError("Expected two finite measurement sequences of length 64.")
    if np.any(counts < 0) or np.any(counts > shots) or np.any(counts != np.floor(counts)):
        raise ValueError("Counts must be integers between zero and shots.")
    return counts.astype(float)


def fit_baseline(counts, shots=SHOTS):
    counts = validate_counts(counts, shots)
    # Scaled rates avoid poor conditioning of optimization in inverse microseconds.
    observed = counts / shots
    least = least_squares(
        lambda z: (probabilities(*(z / 50)) - observed).ravel(), [1, 1], bounds=([0, 0], [20, 20])
    )

    def objective(z):
        p = np.clip(probabilities(*(z / 50)), 1e-10, 1 - 1e-10)
        return -np.sum(counts * np.log(p) + (shots - counts) * np.log1p(-p)) / shots

    fit = minimize(
        objective,
        least.x,
        method="L-BFGS-B",
        bounds=[(0, 20), (0, 20)],
        options={"ftol": 1e-12, "gtol": 1e-8},
    )
    return fit.x / 50, bool(fit.success), str(fit.message)


class PortableMLP:
    """Exact dense/ReLU inference using exported trained weights, without loading both runtimes."""

    def __init__(self, path: Path):
        with np.load(path, allow_pickle=False) as raw:
            self.a = {k: raw[k] for k in raw.files}
        self.metadata = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))

    def predict(self, counts, shots=SHOTS):
        if shots != SHOTS:
            raise ValueError(
                "Neural models are validated for 256 shots and the fixed 64-point grid."
            )
        values = np.asarray(counts, dtype=np.float32).reshape(-1, 128) / shots
        values = (values - self.a["x_mean"]) / self.a["x_std"]
        for i in range(3):
            values = values @ self.a[f"w{i}"] + self.a[f"b{i}"]
            if i != 2:
                values = np.maximum(values, 0)
        log_rates = values * self.a["y_std"] + self.a["y_mean"]
        return np.exp(log_rates)

    def intervals(self, rates):
        q = self.a["calibration_q"]
        return np.stack([rates * np.exp(-q), rates * np.exp(q)], axis=-1)


def diagnose(counts, shots, method, model=None):
    counts = validate_counts(counts, shots)
    start = perf_counter()
    if method == "baseline":
        rates, converged, message = fit_baseline(counts, shots)
        intervals = None
    else:
        if model is None:
            raise ValueError("This trained model is not available. Run the training command first.")
        rates = model.predict(counts, shots)[0]
        intervals = model.intervals(rates).tolist()
        converged, message = True, ""
    elapsed = (perf_counter() - start) * 1000
    return {
        "rates": rates.tolist(),
        "intervals": intervals,
        "converged": converged,
        "message": message,
        "latency_ms": elapsed,
        "curves": probabilities(*rates, TIMES).tolist(),
    }
