"""HTTP application; hosted deployments keep this API on private loopback."""

import hashlib
import json
import os
import re
import secrets
import sqlite3
import threading
import time
from collections import deque
from functools import lru_cache
from pathlib import Path
from typing import Literal

import numpy as np
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from qnd import __version__
from qnd.estimators import PortableMLP, diagnose
from qnd.physics import PROTOCOL, TIMES, derived, sample
from qnd.settings import data_dir, model_dir
from qnd.storage import CapacityError, Repository


class ExperimentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    mode: Literal["mystery", "custom"] = "mystery"
    label: str = Field(default="Quantum experiment", min_length=1, max_length=80)
    gamma1: float | None = Field(default=None, ge=0, le=0.2)
    gamma_phi: float | None = Field(default=None, ge=0, le=0.2)
    shots: int = Field(default=256, ge=16, le=8192, strict=True)
    seed: int | None = Field(default=None, ge=0, le=2**32 - 1, strict=True)

    @model_validator(mode="after")
    def validate_mode(self):
        if self.mode == "custom" and (self.gamma1 is None or self.gamma_phi is None):
            raise ValueError("Custom experiments require both noise rates.")
        if self.mode == "mystery" and (self.gamma1 is not None or self.gamma_phi is not None):
            raise ValueError("Mystery experiments choose their own hidden noise rates.")
        return self


def create_app(db_path: Path | None = None, models_path: Path | None = None,
               public: bool | None = None):
    public = os.environ.get("QND_PUBLIC", "0") == "1" if public is None else public
    app = FastAPI(title="Quantum Noise Detective", version=__version__)
    repo = Repository(db_path or data_dir() / "experiments.sqlite3")
    models = models_path or model_dir()
    app.state.repo = repo
    gate = threading.BoundedSemaphore(2)
    rate_lock = threading.Lock()
    calls = {}

    def visitor(x_qnd_visitor: str | None = Header(default=None)):
        if not public:
            return "local"
        if not x_qnd_visitor or not re.fullmatch(r"[A-Za-z0-9_-]{43}", x_qnd_visitor):
            raise HTTPException(401, "A valid visitor session is required.")
        repo.prune()
        return hashlib.sha256(x_qnd_visitor.encode()).hexdigest()

    def throttle(owner):
        if not public:
            return
        now = time.monotonic()
        with rate_lock:
            for key in list(calls):
                while calls[key] and calls[key][0] <= now - 60:
                    calls[key].popleft()
                if not calls[key]:
                    del calls[key]
            for key, limit in [("global", 300), (owner, 30)]:
                if len(calls.get(key, ())) >= limit:
                    raise HTTPException(429, "The demo is busy. Try again in a minute.")
            for key in ["global", owner]:
                calls.setdefault(key, deque()).append(now)

    @lru_cache(maxsize=2)
    def load_model(method):
        return PortableMLP(models / f"{method}.npz")

    def get(identifier, owner):
        try:
            return repo.get(identifier, owner)
        except KeyError:
            raise HTTPException(404, "Experiment not found") from None

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "version": __version__,
            "protocol": PROTOCOL,
            "models": {
                name: (models / f"{name}.npz").exists() and (models / f"{name}.json").exists()
                for name in ["torch", "tensorflow"]
            },
        }

    @app.get("/ready")
    def ready():
        try:
            with repo.connect() as db:
                db.execute("SELECT count(*) FROM experiments").fetchone()
            for method in ("torch", "tensorflow"):
                rates = load_model(method).predict(np.full((2, 64), 128))
                if not np.all(np.isfinite(rates)) or np.any(rates <= 0):
                    raise ValueError("Invalid model output")
            json.loads((models.parent / "benchmark.json").read_text(encoding="utf-8"))
        except (OSError, ValueError, KeyError, sqlite3.Error):
            raise HTTPException(503, "The lab is not ready.") from None
        return {"status": "ready", "version": __version__}

    @app.post("/experiments", status_code=201)
    def create(request: ExperimentRequest, owner: str = Depends(visitor)):
        throttle(owner)
        seed = request.seed if request.seed is not None else secrets.randbits(32)
        if request.mode == "mystery":
            rng = np.random.default_rng(seed)
            g1 = 1 / np.exp(rng.uniform(np.log(10), np.log(100)))
            gp = 1 / np.exp(rng.uniform(np.log(10), np.log(200)))
        else:
            g1, gp = request.gamma1, request.gamma_phi
        counts = sample(g1, gp, shots=request.shots, seed=(seed + 1) % 2**32)
        measurements = {
            "counts": counts.tolist(),
            "shots": request.shots,
            "times_us": TIMES.tolist(),
            "protocol": PROTOCOL,
            "mode": request.mode,
        }
        truth = {**derived([g1, gp]), "seed": seed, "simulator": "analytic Lindblad solution v1"}
        try:
            return repo.create(request.label, measurements, truth, owner, bounded=public)
        except CapacityError as error:
            raise HTTPException(429, str(error)) from None

    @app.get("/experiments")
    def experiments(owner: str = Depends(visitor)):
        return repo.list(owner)

    @app.get("/experiments/{identifier}")
    def experiment(identifier: str, owner: str = Depends(visitor)):
        return get(identifier, owner)

    @app.post("/experiments/{identifier}/reveal")
    def reveal(identifier: str, owner: str = Depends(visitor)):
        throttle(owner)
        get(identifier, owner)
        return repo.reveal(identifier, owner)

    @app.post("/experiments/{identifier}/diagnose/{method}")
    def infer(identifier: str, method: Literal["baseline", "torch", "tensorflow"],
              owner: str = Depends(visitor)):
        throttle(owner)
        ex = get(identifier, owner)
        if method in ex["diagnoses"]:
            return ex["diagnoses"][method]
        model = None
        if method != "baseline":
            if ex["shots"] != 256:
                raise HTTPException(
                    422, "Neural models support 256 shots only. Use conventional fitting."
                )
            try:
                model = load_model(method)
            except FileNotFoundError:
                raise HTTPException(
                    503, "Model not trained yet. Run the offline training pipeline."
                ) from None
        if not gate.acquire(blocking=False):
            raise HTTPException(429, "The lab is busy. Try again shortly.")
        try:
            result = diagnose(ex["counts"], ex["shots"], method, model)
        finally:
            gate.release()
        result.update(derived(result["rates"]))
        result["method"] = method
        result["model_version"] = model.metadata["model_version"] if model else "binomial-mle-v1"
        result["interval_note"] = (
            "90% marginal split-conformal intervals; calibrated for the simulated "
            "training distribution at 256 shots. Not a joint confidence region."
            if model
            else "Uncertainty intervals are not implemented for the fitting baseline."
        )
        if model:
            result["scope_note"] = (
                "Trained on T1 10–100 µs and Tφ 10–200 µs. "
                "Custom experiments may be outside this distribution; coverage is not guaranteed."
            )
        repo.save_diagnosis(identifier, method, result, owner)
        return result

    @app.get("/benchmark")
    def benchmark():
        path = models.parent / "benchmark.json"
        if not path.exists():
            raise HTTPException(404, "Benchmark not generated yet")
        return json.loads(path.read_text(encoding="utf-8"))

    return app


app = create_app()
