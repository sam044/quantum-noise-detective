"""Frozen-test accuracy, latency, calibration, and explicit distribution-shift stress tests."""

import json
import platform
from time import perf_counter

import numpy as np
from threadpoolctl import threadpool_limits

from qnd.dataset import generate_split
from qnd.estimators import PortableMLP, fit_baseline
from qnd.settings import data_dir, model_dir


def metrics(predictions, truth):
    return {
        "mae_rates": np.mean(np.abs(predictions - truth), axis=0).tolist(),
        "median_relative_error_pct": (
            100 * np.median(np.abs(predictions / truth - 1), axis=0)
        ).tolist(),
    }


def main():
    with np.load(data_dir() / "dataset.npz") as data:
        counts, truth = data["test_counts"], data["test_rates"]
    manifest = json.loads((data_dir() / "dataset.json").read_text())
    report = {
        "n_test": len(counts),
        "dataset": manifest,
        "platform": platform.platform(),
        "parameter_order": ["gamma1", "gamma_phi"],
        "rate_units": "1/microsecond",
        "methods": {},
        "stress_tests": {},
        "notes": [
            "All data is synthetic; ideal readout and time-independent Markovian noise.",
            "Both neural models use the same NumPy inference runtime, one BLAS thread.",
            "Latency is warm single-experiment compute, excluding HTTP, UI and model loading.",
            "Intervals target 90% marginal coverage per rate, not joint coverage.",
            "Stress-test coverage has no conformal guarantee.",
        ],
    }
    with threadpool_limits(limits=1):
        fit_baseline(counts[0])
        estimates, latencies, failures = [], [], 0
        for c in counts:
            start = perf_counter()
            estimate, success, _ = fit_baseline(c)
            latencies.append((perf_counter() - start) * 1000)
            estimates.append(estimate)
            failures += not success
        report["methods"]["baseline"] = {
            **metrics(np.array(estimates), truth),
            "median_latency_ms": float(np.median(latencies)),
            "p95_latency_ms": float(np.percentile(latencies, 95)),
            "failures": failures,
            "coverage": None,
        }
        print("Baseline evaluated", flush=True)
        for name in ["torch", "tensorflow"]:
            start = perf_counter()
            model = PortableMLP(model_dir() / f"{name}.npz")
            load_ms = (perf_counter() - start) * 1000
            predicted = model.predict(counts)
            intervals = model.intervals(predicted)
            covered = (truth >= intervals[:, :, 0]) & (truth <= intervals[:, :, 1])
            model.predict(counts[0])
            times = []
            for c in counts:
                start = perf_counter()
                model.predict(c)
                times.append((perf_counter() - start) * 1000)
            regimes = []
            for j, parameter in enumerate(["gamma1", "gamma_phi"]):
                for k, indexes in enumerate(np.array_split(np.argsort(truth[:, j]), 3)):
                    regimes.append(
                        {
                            "parameter": parameter,
                            "rate_tertile": k + 1,
                            "n": len(indexes),
                            "coverage": float(covered[indexes, j].mean()),
                        }
                    )
            report["methods"][name] = {
                **metrics(predicted, truth),
                "median_latency_ms": float(np.median(times)),
                "p95_latency_ms": float(np.percentile(times, 95)),
                "artifact_load_ms": load_ms,
                "coverage": covered.mean(0).tolist(),
                "mean_interval_width": (intervals[:, :, 1] - intervals[:, :, 0]).mean(0).tolist(),
                "coverage_by_regime": regimes,
                "metadata": model.metadata,
            }
            for condition in ["64_shots", "outside_training_range", "readout_mismatch"]:
                shots = 64 if condition == "64_shots" else 256
                ranges = (
                    {"t1_range": (110, 200), "phi_range": (220, 400)}
                    if condition == "outside_training_range"
                    else {}
                )
                c, y = generate_split(160, 775, shots=shots, **ranges)
                if condition == "readout_mismatch":
                    from qnd.physics import probabilities

                    p = probabilities(y[:, 0], y[:, 1])
                    c = np.random.default_rng(889).binomial(256, 0.05 + 0.9 * p)
                # Deliberate stress-only bypass of production's fixed-shot guard.
                pred = model.predict(c / shots * 256)
                ci = model.intervals(pred)
                report["stress_tests"].setdefault(condition, {})[name] = {
                    **metrics(pred, y),
                    "n": len(y),
                    "coverage": ((y >= ci[:, :, 0]) & (y <= ci[:, :, 1])).mean(0).tolist(),
                }
            print(f"{name} evaluated", flush=True)
    (data_dir() / "benchmark.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                name: {
                    k: v
                    for k, v in results.items()
                    if k
                    in [
                        "mae_rates",
                        "median_relative_error_pct",
                        "coverage",
                        "median_latency_ms",
                        "failures",
                    ]
                }
                for name, results in report["methods"].items()
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
