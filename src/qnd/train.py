"""Offline training: python -m qnd.train --framework torch|tensorflow."""

import argparse
import copy
import hashlib
import json
import os
import platform
import subprocess
import time

import numpy as np

from qnd.dataset import make_dataset
from qnd.estimators import PortableMLP
from qnd.physics import SHOTS
from qnd.settings import data_dir, model_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework", choices=["torch", "tensorflow"], required=True)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--train-size", type=int, default=6000)
    args = parser.parse_args()
    os.environ.setdefault("OMP_NUM_THREADS", "2")
    os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "2")
    os.environ.setdefault("TF_NUM_INTEROP_THREADS", "1")
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    path = data_dir() / "dataset.npz"
    if not path.exists():
        print(json.dumps(make_dataset(path, args.train_size)), flush=True)
    with np.load(path) as raw:
        data = {k: raw[k] for k in raw.files}
    x = data["train_counts"].reshape(-1, 128).astype("float32") / SHOTS
    y = np.log(data["train_rates"]).astype("float32")
    arrays = {
        "x_mean": x.mean(0),
        "x_std": np.maximum(x.std(0), 0.03),
        "y_mean": y.mean(0),
        "y_std": y.std(0),
    }
    x = (x - arrays["x_mean"]) / arrays["x_std"]
    y = (y - arrays["y_mean"]) / arrays["y_std"]
    xv = (
        data["validation_counts"].reshape(-1, 128).astype("float32") / SHOTS - arrays["x_mean"]
    ) / arrays["x_std"]
    yv = (np.log(data["validation_rates"]).astype("float32") - arrays["y_mean"]) / arrays["y_std"]
    rng = np.random.default_rng(42)
    start = time.perf_counter()
    best_loss, stale, history = float("inf"), 0, []
    if args.framework == "torch":
        import torch

        torch.set_num_threads(2)
        torch.manual_seed(42)
        net = torch.nn.Sequential(
            torch.nn.Linear(128, 128),
            torch.nn.ReLU(),
            torch.nn.Linear(128, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, 2),
        )
        opt = torch.optim.Adam(net.parameters(), lr=0.001, weight_decay=1e-5)
        tx, ty, tv = map(torch.from_numpy, [x, y, xv])
        best = copy.deepcopy(net.state_dict())
        for epoch in range(args.epochs):
            net.train()
            for batch in np.array_split(rng.permutation(len(x)), max(1, len(x) // 256)):
                opt.zero_grad()
                loss = ((net(tx[batch]) - ty[batch]) ** 2).mean()
                loss.backward()
                opt.step()
            net.eval()
            with torch.no_grad():
                val = float(((net(tv) - torch.from_numpy(yv)) ** 2).mean())
            history.append(val)
            if val < best_loss - 1e-5:
                best_loss, stale, best = val, 0, copy.deepcopy(net.state_dict())
            else:
                stale += 1
            if epoch % 10 == 0:
                print(f"epoch={epoch + 1} validation_loss={val:.5f}", flush=True)
            if stale >= 15:
                break
        net.load_state_dict(best)
        net.eval()
        torch.save(net.state_dict(), model_dir() / "torch.pt")
        for i, layer in enumerate([net[0], net[2], net[4]]):
            arrays[f"w{i}"] = layer.weight.detach().numpy().T
            arrays[f"b{i}"] = layer.bias.detach().numpy()
        with torch.no_grad():
            native = np.exp(net(tv[:32]).numpy() * arrays["y_std"] + arrays["y_mean"])
        framework_version = torch.__version__
    else:
        import tensorflow as tf

        tf.config.threading.set_intra_op_parallelism_threads(2)
        tf.config.threading.set_inter_op_parallelism_threads(1)
        tf.keras.utils.set_random_seed(42)
        net = tf.keras.Sequential(
            [
                tf.keras.Input(shape=(128,)),
                tf.keras.layers.Dense(128, activation="relu"),
                tf.keras.layers.Dense(64, activation="relu"),
                tf.keras.layers.Dense(2),
            ]
        )
        net.compile(optimizer=tf.keras.optimizers.Adam(0.001), loss="mse")
        best = net.get_weights()
        for epoch in range(args.epochs):
            for batch in np.array_split(rng.permutation(len(x)), max(1, len(x) // 256)):
                net.train_on_batch(x[batch], y[batch])
            val = float(np.mean((net(xv, training=False).numpy() - yv) ** 2))
            history.append(val)
            if val < best_loss - 1e-5:
                best_loss, stale, best = val, 0, net.get_weights()
            else:
                stale += 1
            if epoch % 10 == 0:
                print(f"epoch={epoch + 1} validation_loss={val:.5f}", flush=True)
            if stale >= 15:
                break
        net.set_weights(best)
        net.save(model_dir() / "tensorflow.keras")
        for i, layer in enumerate(net.layers):
            arrays[f"w{i}"], arrays[f"b{i}"] = layer.get_weights()
        native = np.exp(net(xv[:32], training=False).numpy() * arrays["y_std"] + arrays["y_mean"])
        framework_version = tf.__version__
    elapsed = time.perf_counter() - start
    try:
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except subprocess.CalledProcessError:
        revision = "uncommitted"
    metadata = {
        "framework": args.framework,
        "framework_version": framework_version,
        "architecture": [128, 128, 64, 2],
        "activation": "relu",
        "epochs": len(history),
        "best_validation_mse": best_loss,
        "validation_history": history,
        "training_seconds": elapsed,
        "seed": 42,
        "dataset_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_revision": revision,
        "python": platform.python_version(),
        "runtime": "NumPy dense/ReLU export; parity-checked against native framework",
        "coverage_target": 0.9,
        "interval_method": "split conformal absolute log-rate residual",
        "interval_scope": "marginal per rate; in-distribution 256-shot experiments only",
    }
    output = model_dir() / f"{args.framework}.npz"
    arrays["calibration_q"] = np.zeros(2)
    np.savez(output, **arrays)
    output.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    model = PortableMLP(output)
    exported = model.predict(data["validation_counts"][:32])
    np.testing.assert_allclose(exported, native, rtol=2e-5, atol=1e-7)
    predictions = model.predict(data["calibration_counts"])
    scores = np.abs(np.log(predictions) - np.log(data["calibration_rates"]))
    rank = min(len(scores), int(np.ceil((len(scores) + 1) * 0.9)))
    arrays["calibration_q"] = np.sort(scores, axis=0)[rank - 1]
    np.savez(output, **arrays)
    metadata["export_max_absolute_error"] = float(np.max(np.abs(exported - native)))
    metadata["artifact_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    metadata["model_version"] = args.framework + "-" + metadata["artifact_sha256"][:10]
    output.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Saved {output}; training={elapsed:.1f}s; export parity passed", flush=True)


if __name__ == "__main__":
    main()
