# Quantum Noise Detective — new-chat handoff

Updated 2026-09-13. This is a project handoff, not a full conversation export.
The original local handoff is retained below with subsequent deployment and publication updates.

## Start here and next objective

Deployment update 2026-09-13: Sam bought `samuelflynn.dev`, signed into Railway,
approved $10-15/month hosting, and personally activated Hobby billing. The app
is deployed at **https://quantum.samuelflynn.dev**. See `docs/OPERATIONS.md`
for exact resources, deployment, backups and recovery. The usage guide and
detailed video explanation remain deferred at Sam's request.

GitHub publication update 2026-09-13: the source is public at
https://github.com/sam044/quantum-noise-detective. The default branch is
`initial-release` (renamed from `codex/initial-release` at Sam's request), tracked by local remote `origin`. Initial source commit
`535068d` was pushed successfully. Credentials, generated models, datasets and
SQLite history are excluded. GitHub Actions was queued after publication;
remote validation has not yet been confirmed. Railway remains deployed from
the existing release; publishing this repository did not configure automatic deployment.

Current deployment: `850dbd1e-7bd2-4a3d-99a7-280dfdfdfecd`, Railway SUCCESS.
The custom domain is verified with a valid managed HTTPS certificate. DNS uses
a Cloudflare DNS-only CNAME and Railway's verification TXT record. Root and www
have no site configured. Railway has one container, a /data volume, a 1 GB RAM /
1 vCPU limit, $10 usage alert and $15 hard workspace usage limit.

Implementation: public anonymous session ownership enforced by API, migration
preserving local history, 7-day active public history, per-session/global limits,
cached diagnoses, bounded concurrent inference, pinned Linux serving image,
artifact hash validation, service supervision/readiness, daily SQLite backups.
Models are under /app/artifacts/models, database under /data. The full native
models and datasets remain untouched outside the local checkout.

Verified in this deployment session: 26 Windows tests; 16 API/public-release
checks in Linux; dependency consistency; actual hosted 5-visitor/15-diagnosis
flow; cross-visitor denial; database persistence after redeployment; consistent
backup and isolated restore; downloaded backup integrity; local container crash
recovery. Initial hosted memory observation approximately 229 MB; short sample,
not a monthly cost forecast. Browser validation is recorded in DEPLOYMENT_VALIDATION.

Hobby UI limits managed backups to Pro. Daily SQLite backups are on the SAME
volume (7 snapshots); a verified additional backup was downloaded locally.
Automatic off-volume backups and external uptime alerts are not configured.
Do not claim either. Use OPERATIONS for the limitation and manual procedure.
Local source/model/history backup: C:\Users\sam\.quantum-noise-detective-backups\20260913-204827.
Release staging directories: C:\Users\sam\.quantum-noise-detective-release\20260913-1 and -2.
The Railway CLI is installed and signed in. A dedicated SSH key is outside the
checkout at C:\Users\sam\.ssh\qnd_railway. Never publish credentials.

The sections below describe the earlier local handoff; deployment statements
there are historical and superseded by this update.

The user wants a finished, publicly deployed portfolio product and eventually a
GitHub repository. They asked to preserve context now and will give new
deployment instructions in the next chat. Read those instructions before acting.
The requested sequence is finish the product, deploy, then prepare GitHub.
Do not silently require public GitHub publication as the first step: discuss any
source repository or image registry required by the chosen deployment approach.

Sam has no Python/neural-network experience and wants an agent-led process with
minimal interruptions. Explain accounts, costs, and any user-only steps clearly.
The original 1–2 day target was for a prototype, not proof of production readiness.

Suggested first message in a new chat opened in the same project folder:

> Read AGENTS.md and docs/HANDOFF.md, then inspect the existing project. Continue
> Quantum Noise Detective from the current implementation. I will provide the
> deployment instructions here. Do not rebuild it from scratch or assume that
> the original project plan exactly describes what is implemented.

## Current product

Working local release, version 0.1.0:

- Streamlit/Plotly interface: experiment lab, model comparison, history, field guide.
- Mystery/custom noise generation, conventional/PyTorch/TensorFlow diagnosis,
  calibrated neural intervals, explicit truth reveal, saved experiments and JSON export.
- Interactive measurement plots and a Bloch-sphere field-guide visualization.
- FastAPI API, Pydantic validation, SQLite persistence, reproducible offline ML.
- No Qiskit, quantum hardware, hosted AI calls, or application API keys.

Architecture: Streamlit -> FastAPI -> physics/estimators and SQLite/model artifacts.
Training is offline. Serving uses a shared lightweight NumPy MLP implementation;
it does not load PyTorch and TensorFlow for each request. Both frameworks really
were used to train models, with native/export parity checks.

## Scientific contract and limitations

- One qubit, zero-temperature energy relaxation and pure dephasing, constant rates.
- Infer gamma1 and gamma_phi in inverse microseconds; gamma2 = gamma1/2 + gamma_phi.
- Separate preparations measure excited-state population decay and X-basis
  coherence decay. These are aggregated fresh-shot experiments, not continuous
  measurements of one qubit. Population alone cannot identify pure dephasing.
- QuTiP is an independent Lindblad reference; vectorized analytic solutions
  generate the dataset and demo efficiently.
- Fixed 64-delay grid, 0–300 microseconds. Neural inference supports 256 shots
  only. Other supported shot counts use conventional fitting.
- Training ranges: T1 10–100 us, Tphi 10–200 us. Custom settings may be outside them.
- Uncertainty is log-rate split-conformal calibration with separate calibration
  data: nominal 90% marginal intervals, not joint or out-of-distribution guarantees.
- Baseline uses binomial maximum likelihood. Baseline uncertainty is NOT implemented.
- Conventional fitting was more accurate; neural NumPy inference was faster.
  Do not claim quantum computational advantage or real-device validation.

The original plan proposed bootstrap baseline intervals, an ensemble/quantile
model, and another package layout. Those are not the implemented local design.
The actual package is `src/qnd`, and the actual release decisions above take
precedence when describing existing functionality.

## Locations and artifacts — do not lose these

| Item | Location on this machine |
| --- | --- |
| Checkout | `C:\Users\sam\OneDrive\Desktop\Quantum Project` |
| Python | `C:\Users\sam\.venvs\quantum-noise-detective\Scripts\python.exe` |
| Default runtime data | `C:\Users\sam\.quantum-noise-detective` |
| Separate reproduction data | `C:\Users\sam\.quantum-noise-detective-reproduction` |
| API | `http://127.0.0.1:8765` |
| Dashboard | `http://127.0.0.1:8501/` |

Runtime data was verified to include `dataset.npz`, `dataset.json`,
`benchmark.json`, `experiments.sqlite3` and SQLite WAL/SHM files, plus `models/`:
`torch.npz`, `torch.json`, `torch.pt`, `tensorflow.npz`, `tensorflow.json`,
`tensorflow.keras`. Serving requires the NPZ/JSON pairs; the benchmark endpoint
reads runtime `benchmark.json`. Native training artifacts and dataset should be
preserved for reproducibility but need not all be in a serving image.

`QND_DATA_DIR` overrides runtime data location. `QND_API_URL` configures the
dashboard's server-side API URL (default loopback:8765). Logs from the supervisor
are under the default runtime directory's `logs/`; their location is currently
independent of `QND_DATA_DIR`.

Copying only the project folder does NOT copy the trained models or history.
For a new machine/deployment, deliberately package or regenerate model artifacts.
Use SQLite's backup facilities or stop writers before backing up live history;
do not assume copying only the main database while WAL is active is sufficient.

## Local startup fix, 2026-09-13

The app twice became unreachable because neither service was running. Windows
had not rebooted between the latest starts, and old logs did not establish why
the processes stopped. Do not present a specific crash cause as proven.

Current solution:

- Windows task `Quantum Noise Detective`, interactive current-user account,
  limited privileges, starts at sign-in and repeats every minute. IgnoreNew
  prevents concurrent task instances; there is no execution time limit and it
  is allowed on battery. It restarts on failure and starts when available.
- Task runs the venv `pythonw.exe` with `launch.py --no-browser`, in the checkout.
- `launch.py` supervises API/dashboard exits with bounded retry delays. An
  exclusive loopback socket on 8766 prevents duplicate supervisors. A new
  supervisor reuses healthy services left by its predecessor.
- `Start Lab.cmd` / `Start-Lab.ps1` use `--background` and open a browser without
  requiring a terminal to remain open. No-browser invocation reuses an existing
  supervisor rather than starting duplicate servers.
- `scripts/Install-Autostart.ps1` installs/reinstalls the task. Read it before
  changing machine configuration. Moving the checkout/venv requires updating it.
- Logs: `logs/supervisor.log`, `logs/api.log`, `logs/dashboard.log`.

This handles process exits, not every possible hung service or machine failure.
It is local availability while signed in and awake, not public hosting. Disable
automatic startup with `Disable-ScheduledTask -TaskName 'Quantum Noise Detective'`;
signing out stops the session's services. Merely killing a service may cause it
to be restarted. Target only verified project processes when troubleshooting.

## Verification: distinguish dates and scope

Recorded 2026-09-11 in `docs/VALIDATION.md`:

- 22 pytest tests passed, including two actual-trained-model API integration tests.
- Physics/QuTiP agreement, deterministic sampling/splits, fitting recovery,
  validation, hidden truth, persistence, and model parity were checked.
- Independent data-directory reproduction in the SAME installed environment
  produced identical dataset hashes and exported arrays. Not a clean-machine test.
- Browser flow, estimators, reveal/history, benchmark, JSON download and field
  guide were checked in narrow and desktop layouts.

Verified during startup repair on 2026-09-13:

- Deliberately stopped the supervisor; the scheduled task restarted it.
- Deliberately stopped both service trees; the supervisor restored service health.
- Duplicate no-browser launch exited without starting another supervisor.
- Ruff check passed for `launch.py`; task settings were inspected.

Verified again while writing this handoff on 2026-09-13:

- Task state: Running. API health: ok, version 0.1.0, protocol paired-decay-v1,
  both model artifact pairs present. Dashboard health: ok.
- Listed the actual runtime/model artifacts and read implementation/configuration.
- Full training/tests and browser visual inspection were NOT rerun for this
  documentation task. These runtime observations are snapshots, not guarantees.

Benchmark evidence: `docs/BENCHMARK.md`, `docs/BENCHMARK.json`,
`docs/VALIDATION.md`. Recorded 800-test median relative errors for gamma1/gamma_phi:
baseline 1.07%/7.20%, PyTorch 2.20%/7.34%, TensorFlow 3.31%/10.38%.
Shared NumPy serving timings exclude HTTP/UI and vary with machine load.

## Commands

From the checkout in PowerShell:

```powershell
$labPython = 'C:\Users\sam\.venvs\quantum-noise-detective\Scripts\python.exe'
& $labPython -m pytest -q
& $labPython -m ruff check src tests dashboard scripts launch.py
& $labPython launch.py --background
```

Offline operations, only when needed (training updates artifacts):

```powershell
& $labPython -m qnd.train --framework torch
& $labPython -m qnd.train --framework tensorflow
& $labPython -m qnd.evaluate
& $labPython scripts/reproduce.py
```

Reproduction defaults to a separate directory, but honors an existing
`QND_DATA_DIR`; check that variable before running. API model loads are cached;
restart the API after intentionally replacing model exports.

Python is constrained to 3.12 in `pyproject.toml`. The exact dependency snapshot
is Windows-specific (`requirements-lock-windows-py312.txt`), not a verified Linux
lock. Clean installs also need `pip install -e . --no-deps` after dependencies.

## Public-release planning still required

No cloud deployment, Docker configuration, hosting account, domain, or billing
has been configured by this project. Render/Docker was mentioned as a possible
route earlier, but no provider or budget was selected. Verify current hosting
documentation and prices before recommending accounts or commitments.

Inspect and plan these areas before calling it a finished public product:

1. Define a reviewable release scope and polish/retest the complete user journey.
2. Resolve visitor isolation: current experiment list/storage are shared and
   unauthenticated. Decide intentional public demo history versus session/account
   ownership, including reveal and saved diagnoses. Do not blindly expose local API.
3. Package CPU serving dependencies and versioned models; validate installation
   and inference in the target host environment. Do not train in web requests.
4. Configure public HTTPS ingress, Streamlit websocket support, API routing,
   environment variables, readiness and process lifecycle for the chosen host.
5. Decide persistent storage, retention/backups, bounded public resource usage,
   concurrent visitors, useful errors, logs, and restart/redeploy behavior.
6. Test the hosted URL from outside this computer and verify state behavior across
   restarts before declaring deployment complete. Document costs and ownership.

These are planning items, not accepted implementation choices. Avoid adding
accounts, infrastructure, or features simply because they appear in this list.
The user will give the new instructions in the next chat.

## Git and document map

Verified: local Git repository on unborn `master`, no commits, no remotes, all
project files untracked. No GitHub publication and no remote CI execution.
Preserve the whole working directory; there is no committed restore point.
Use `codex/` for future new branches unless user instructions specify otherwise.

`.github/workflows/verify.yml` prepares Windows install/lint/train/test and
artifact upload. It has not been run remotely. Review artifacts and publication
scope before enabling it or uploading data. `.gitignore` excludes common local
credentials, environments and runtime outputs.

- `README.md`: user-facing overview and commands.
- `docs/PROJECT_PLAN.md`: historical scientific/product plan.
- `docs/PROGRESS.md`: local release decisions and progress.
- `docs/SETUP.md`: original machine setup, with dated limitations.
- `docs/VALIDATION.md`: historical test and browser evidence.
- `docs/BENCHMARK.md` / `.json`: measured results and caveats.
- `docs/DEMO.md`: demo/interview guidance.
- `src/qnd/`: physics, dataset, estimators, training, evaluation, API, settings, storage.
- `dashboard/app.py`, `tests/`, `scripts/`: UI, checks, reproduction and autostart.

Keep this chat for reference if useful. The same project folder, this handoff,
and the user's next instructions are sufficient to resume; do not rely on an
assumption that a new chat automatically inherits all previous conversation text.
