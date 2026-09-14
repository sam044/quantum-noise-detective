# Demo and interview guide

## A 90-second walkthrough

1. Open Experiment lab. Expand Configure an experiment, choose Mystery noise and 256 shots, and generate an experiment.
2. Explain the two charts: one measures energy loss; the other measures coherence. Each delay uses a finite number of freshly prepared qubits.
3. Click Compare methods. Select the PyTorch model to show its parameter intervals.
4. Click Reveal truth. Compare the hidden parameters and simulator curves with the predictions.
5. Open Model comparison. Show the measured tradeoff: conventional fitting is more accurate; exported neural inference is faster. Acknowledge the stress-test limitations.
6. Open Experiment history and reopen the saved experiment.
7. In Field guide, move the time slider and rotate the Bloch sphere.

## Explain your work honestly

"I built an agent-assisted Python application that estimates relaxation and dephasing rates from simulated quantum measurements. I specified the product, used an AI coding agent for implementation, and can explain the measurement design, evaluation, and software architecture."

For an interview, learn these five points:

- T1 measures energy relaxation; Tphi measures pure dephasing; both determine T2.
- Population measurements alone cannot identify dephasing, so the system uses two protocols.
- Training, validation, calibration, and test configurations are independent.
- Conventional fitting is a serious baseline; the project does not assume ML must win.
- Synthetic-data performance and interval coverage do not automatically transfer to hardware.

## Resume bullet draft

Built a Python quantum-noise diagnosis platform with FastAPI, Streamlit, SQLite, and PyTorch/TensorFlow models; evaluated against binomial maximum-likelihood fitting on 800 unseen simulated experiments, with calibrated parameter intervals and an interactive physics dashboard.

Use numeric latency/error claims only with benchmark context. Both neural models use NumPy serving; do not describe those timings as native framework benchmarks or a quantum speedup.

## Launch and stop

Use README.md's launch command. Keep that process running while viewing the app. Ctrl+C stops both services; history remains on disk. If another process occupies port 8501 or 8765, stop the earlier lab instance first. The launcher does not terminate unrelated programs.

No paid API or account is required. Public hosting and GitHub publication are separate from this local release.
