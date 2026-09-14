# Setup guide

## Machine inspection: 2026-09-11

- Windows, PowerShell.
- Python 3.12.4 and Python 3.14 installed. Use 3.12 explicitly for this project.
- Git 2.53.0 installed.
- Approximately 7.8 GiB usable physical RAM and Intel Iris Xe integrated graphics.
- Approximately 72.9 GiB free on C: at inspection.
- Docker CLI exists; the Docker engine has not been tested and is not required now.
- The project folder was empty and was not a Git repository at initial inspection.

## Environment choice

Use native Windows with CPU packages. Small single-qubit datasets and compact neural networks are designed to make this practical; actual training times will be measured in the pilot.

Environment path:

    C:\Users\sam\.venvs\quantum-noise-detective

Source/documentation path:

    C:\Users\sam\OneDrive\Desktop\Quantum Project

The environment lives outside OneDrive to avoid syncing installed dependencies. It is isolated from your other Python projects. No global Python-package changes or PowerShell execution-policy changes are needed.

TensorFlow's official guide says modern native-Windows releases do not support CUDA GPU execution. CPU execution avoids WSL/CUDA setup for now. See the [official installation guide](https://www.tensorflow.org/install/pip).

## Stack and purpose

| Component | Purpose |
| --- | --- |
| Python 3.12 | Main language and runtime |
| NumPy and SciPy | Arrays, analytic physics, sampling, conventional fitting |
| QuTiP | Independent quantum-dynamics reference simulator |
| PyTorch, CPU | Main neural estimator |
| TensorFlow/Keras, CPU | Equivalent comparison model |
| scikit-learn | Data preprocessing and evaluation helpers |
| FastAPI, Pydantic, Uvicorn | Validated Python HTTP API and server |
| Streamlit and Plotly | Python dashboard and interactive charts |
| SQLite via Python's sqlite3 | Local experiment history; no separate installation |
| HTTPX | Dashboard API calls and API checks |
| pytest and Ruff | Tests and linting |
| Git | Source version history |

GitHub Actions is planned when a remote repository exists. Docker packaging and public hosting can follow the working local demo.

## Commands for this machine

These PowerShell examples use the environment's interpreter directly, so activation is optional.

Check the environment:

```powershell
& 'C:\Users\sam\.venvs\quantum-noise-detective\Scripts\python.exe' --version
& 'C:\Users\sam\.venvs\quantum-noise-detective\Scripts\python.exe' -m pip check
```

To recreate it at a NEW path on Windows, first install 64-bit Python 3.12 if missing, create an environment, and install the CPU PyTorch wheel before other packages. Do not overwrite a working environment just to repeat setup.

```powershell
py -3.12 -m venv 'C:\Users\sam\.venvs\quantum-noise-detective'
& 'C:\Users\sam\.venvs\quantum-noise-detective\Scripts\python.exe' -m pip install --upgrade pip
& 'C:\Users\sam\.venvs\quantum-noise-detective\Scripts\python.exe' -m pip install torch --index-url https://download.pytorch.org/whl/cpu
& 'C:\Users\sam\.venvs\quantum-noise-detective\Scripts\python.exe' -m pip install -r 'C:\Users\sam\OneDrive\Desktop\Quantum Project\requirements.txt'
```

The verified requirements-lock-windows-py312.txt records exact installed package versions. To reproduce that snapshot in a fresh Python 3.12 environment, use:

```powershell
& 'C:\Users\sam\.venvs\quantum-noise-detective\Scripts\python.exe' -m pip install -r 'C:\Users\sam\OneDrive\Desktop\Quantum Project\requirements-lock-windows-py312.txt' --extra-index-url https://download.pytorch.org/whl/cpu
```

The snapshot is specific to Windows/Python 3.12 and is not a cross-platform or hash-verified lock. Dependency checks and import/arithmetic smoke checks validate setup; application tests do not exist yet.

## Completed setup and verification

Completed on 2026-09-11:

- Created the isolated Python 3.12.4 environment at the path above.
- Upgraded pip inside this environment and installed all direct dependencies.
- Installed PyTorch 2.14.0+cpu and TensorFlow 2.21.0.
- Verified both frameworks with a basic arithmetic and automatic-gradient calculation; both returned the expected gradient.
- Installed NumPy 2.5.3, SciPy 1.18.1, and QuTiP 5.3.1; checked a SciPy matrix exponential and QuTiP matrix operation.
- Imported scikit-learn, FastAPI, Pydantic, Uvicorn, Streamlit, Plotly, HTTPX, and pytest successfully.
- Verified an in-memory SQLite query.
- Ran pip check: no broken requirements found.
- Saved exact installed dependency versions in requirements-lock-windows-py312.txt.
- Initialized a local Git repository and added ignore rules. No commit, GitHub repository, or publication was created.

Observed limitations: first imports were slow, especially TensorFlow, and available RAM was low during inspection. Run models sequentially and measure pilot training before scaling. TensorFlow confirmed CPU execution and warned that native-Windows GPU execution is unavailable.

QuTiP emitted a warning that its optional Matplotlib graphics are unavailable. Its numerical check passed. Plotly is installed for planned dashboard charts; add Matplotlib later only if QuTiP-specific plots or static publication figures are needed.

These checks verify the environment, not the future simulator's physics or model performance. Those checks belong to the implementation milestones.

## Accounts, keys, and user actions

**Nothing needs purchasing or signing up for to begin. No API keys are needed.** Training data is generated locally. This project does not call OpenAI, IBM Quantum, or another hosted model API.

Later, for publishing your portfolio:

1. Use or create a personal GitHub account if you want the code hosted there.
2. Sign in yourself when authentication is needed. Never paste account passwords or tokens into the chat or source files.
3. Choose public versus private visibility when we are ready to publish. Local setup does not create or publish a remote repository.

No editor installation is required to continue here. If using an external editor, select the Python executable at the environment path above.

Confirmed planning input: no Python/neural-network experience, desired prototype in 1-2 days, and agent-led technical decisions. No additional setup answers are required. The assistant will explain relevant concepts while implementing after the planning discussion.

## Implementation status

The planning-only phase is complete. The application, simulator, training pipeline, and dashboard are implemented. See README.md for launch commands and docs/PROGRESS.md for the latest validation record. The environment notes above describe the original setup inspection.
