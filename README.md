# Quantum Noise Detective

**Live demo:** [quantum.samuelflynn.dev](https://quantum.samuelflynn.dev)

Hosted usage: open the demo, generate an experiment, compare methods, then reveal the simulator truth. Download JSON to keep results. Public history belongs to an anonymous browser session and may become inaccessible after refresh/reconnect. See [hosting and recovery](docs/OPERATIONS.md).

Continuing development in a new chat? Start with [the project handoff](docs/HANDOFF.md)
and the project instructions in [AGENTS.md](AGENTS.md).

Quantum Noise Detective is an interactive lab that asks: **can we work out how a simulated qubit is losing information just by looking at its measurements?** You create an experiment, let three methods diagnose it, and reveal the hidden answer to see how close they came. Everything runs on an ordinary computer; no quantum hardware is needed.

## The idea, without the quantum background

A normal computer bit stores a 0 or a 1. A **qubit** also gives a 0 or 1 when measured in the usual way, but before measurement it can be in a **superposition** of those two states. That state has more structure than a simple probability of getting 0 or 1: it also has a relationship called *phase*, which affects what we observe when we change how we measure it. This choice of how to measure is called the **measurement basis**.

You do not need to calculate any of this to use the lab. Think of a qubit as carrying two things we want to preserve: its energy and its quantum coherence. This project simulates two ways they can deteriorate:

| Type of noise | Intuition | What the lab estimates |
| --- | --- | --- |
| **Energy relaxation** | Like a charged battery gradually losing energy, an excited qubit can fall back to its lower-energy state. | How quickly that energy is lost. |
| **Pure dephasing** | Like clocks drifting out of sync across repeated experiments, the phase becomes less consistent, weakening the observable quantum pattern without directly changing the energy populations. | How quickly that phase consistency is lost. |

These are analogies for the simulated behavior. The simulator uses a specific mathematical model of a single qubit, rather than a complete model of every noise source in a real quantum computer.

## How an experiment works

1. **Set up a mystery.** The simulator chooses hidden rates for relaxation and dephasing, or you choose them yourself in custom mode. Those rates are the answer the diagnosis methods will try to recover.
2. **Collect two sets of clues.** One experiment prepares the qubit in its excited state and checks how much excited-state population remains after different delays. The other prepares a superposition and measures in a different basis to track its coherence. Both relaxation and pure dephasing affect coherence, so the energy experiment helps separate their contributions. Energy measurements alone cannot reveal pure dephasing.
3. **Repeat the measurements.** A single measurement gives one outcome, not a smooth curve. By default, the simulator repeats each preparation-and-measurement experiment 256 times at each of 64 delays. Each repetition is called a **shot**. The resulting counts fluctuate naturally, so the methods must work with imperfect clues.
4. **Compare three diagnoses.** Conventional statistical fitting searches for noise rates that make the observed counts most likely under the physics model. Two neural networks, trained separately in **PyTorch** and **TensorFlow**, learn the connection between measurement patterns and noise rates from synthetic examples with known answers. They then estimate rates for a new experiment from its counts. The hidden answer is never an input to any diagnosis method.
5. **Reveal and check.** Compare the estimated rates and reconstructed curves, inspect the neural models' uncertainty intervals, then reveal the simulator's true rates. Those intervals are calibrated on separate examples; they are not a promise that every answer falls inside them. Export the results as JSON if you want to keep them.

**Larger rates mean faster deterioration.** The dashboard also shows characteristic times: **T1** describes energy relaxation, **Tφ** describes pure dephasing, and **T2** describes coherence loss from both effects together. Longer times mean the corresponding property lasts longer.

The point is to compare a physics-based fitting method with learned shortcuts on the same task. In the recorded benchmark below, conventional fitting gives the smallest errors, while the neural models produce estimates faster. This is a simulation and machine-learning comparison, not a claim of quantum-computational speedup or validation on real hardware.

## Run on this machine

Double-click **Start Lab.cmd** in this folder. It starts the lab in the background and opens your browser; no terminal needs to stay open. Repeated launches reuse the running lab.

On Sam's computer, the **Quantum Noise Detective** Windows scheduled task starts the lab at sign-in and checks every minute that the launcher is running. The launcher restarts services that exit, with a short delay between retries. No administrator privileges or stored password are required. The app is unavailable while Windows is asleep, shut down, or signed out; this is still local hosting.

To reinstall automatic startup, run `powershell -ExecutionPolicy Bypass -File scripts\Install-Autostart.ps1` from this folder. To disable automatic startup, run `Disable-ScheduledTask -TaskName 'Quantum Noise Detective'`; signing out then stops the current session's services. Logs are in `%USERPROFILE%\.quantum-noise-detective\logs`. Moving the project or its Python environment requires updating/reinstalling the task.

Open PowerShell in this project folder and run:

```powershell
& "$env:USERPROFILE\.venvs\quantum-noise-detective\Scripts\python.exe" launch.py
```

This starts the API and dashboard, opens the browser, and keeps both services running until Ctrl+C. The dashboard is at [localhost:8501](http://127.0.0.1:8501); interactive API documentation is at [localhost:8765/docs](http://127.0.0.1:8765/docs).

**No API keys, quantum hardware, cloud account, or paid service is required.** Source and configuration live here; generated data, models, and experiment history live in `~/.quantum-noise-detective/`. Set `QND_DATA_DIR` to change that location.

## Explore

- **Experiment lab:** mystery or custom noise, binomial measurement samples, fitting/neural inference, parameter intervals, reveal, JSON export.
- **Model comparison:** 800 frozen test experiments, latency, interval coverage, and distribution-shift stress tests.
- **Experiment history:** persisted measurements, model versions, diagnoses, and reveal status.
- **Field guide:** plain-language physics and an interactive Bloch-sphere trajectory.

Measurements use two preparations: excited-state population decay and X-basis coherence decay. Energy measurements alone cannot identify pure dephasing. All data is synthetic under a specified idealized noise model.

## Recorded benchmark

One local CPU run; 800 test experiments, 256 shots per delay, fixed 64-point grid. Relative errors are medians for the two rates, not prediction accuracy percentages.

| Estimator | Relaxation-rate error | Dephasing-rate error | Median compute |
| --- | ---: | ---: | ---: |
| Conventional binomial fit | 1.07% | 7.20% | 14.88 ms |
| PyTorch-trained MLP | 2.20% | 7.34% | 0.070 ms |
| TensorFlow-trained MLP | 3.31% | 10.38% | 0.070 ms |

Conventional fitting is most accurate; neural inference is faster. **Both neural models use the same lightweight NumPy serving runtime**, numerically checked against the native framework outputs. Latencies exclude loading, HTTP, and UI work and vary by machine. One of 800 conventional fits reported non-convergence; its finite output is included in the error summary.

PyTorch's nominal 90% marginal intervals covered 91.75% of relaxation rates and 88.00% of dephasing rates. TensorFlow's covered 92.375% and 89.25%. These are empirical results, not guaranteed coverage for every regime. See [benchmark report](docs/BENCHMARK.md) and [raw results](docs/BENCHMARK.json).

## Install elsewhere

Use 64-bit Python 3.12. The exact snapshot is for Windows/Python 3.12; other platforms should resolve the direct dependencies in `requirements.txt`.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock-windows-py312.txt --extra-index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
.\.venv\Scripts\python.exe -m qnd.train --framework torch
.\.venv\Scripts\python.exe -m qnd.train --framework tensorflow
.\.venv\Scripts\python.exe -m qnd.evaluate
.\.venv\Scripts\python.exe launch.py
```

Training uses separate processes and compact dense networks. Saved artifacts are generated locally and excluded from Git. The API can run conventional fitting before models exist; restart it after retraining to reload cached exports.

## Development and reproducibility

```powershell
python -m pytest -q
python -m ruff check src tests dashboard scripts launch.py
python scripts/reproduce.py
```

Use the project's Python interpreter. The reproduction script generates a separate dataset, trains, evaluates, and tests in `~/.quantum-noise-detective-reproduction/` unless `QND_DATA_DIR` is set. It does not overwrite live experiments by default. Twenty tests do not require trained models; two integration tests use actual trained artifacts. GitHub Actions is configured to install, train, evaluate, and test on Windows when the repository is published.

## Architecture

```mermaid
flowchart LR
  UI[Streamlit and Plotly] --> API[FastAPI]
  API --> Physics[Validated simulator]
  API --> Fit[SciPy binomial fitting]
  API --> ML[Exported neural inference]
  API --> DB[(SQLite history)]
  Train[Offline PyTorch and TensorFlow training] --> ML
  Data[Reproducible synthetic datasets] --> Train
  Data --> Eval[Held-out evaluation and calibration]
```

Core code is in `src/qnd/`; the dashboard is in `dashboard/app.py`. There is no Qiskit code and no claimed quantum-computational speedup.

- [Project plan](docs/PROJECT_PLAN.md)
- [Setup and environment](docs/SETUP.md)
- [Demo and interview guide](docs/DEMO.md)
- [Build progress](docs/PROGRESS.md)

This release runs locally and on Railway through a pinned Linux Docker image. Hardware validation and baseline uncertainty intervals are not included. See [deployment validation](docs/DEPLOYMENT_VALIDATION.md) for current evidence and hosting limitations.
