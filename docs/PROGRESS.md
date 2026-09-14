# Build progress

## Public deployment — 2026-09-13

Deployed to https://quantum.samuelflynn.dev on Railway Hobby, with Cloudflare DNS.
Added backend visitor ownership, bounded demo usage, pinned Linux serving package,
readiness/supervision, artifact validation and SQLite-consistent daily backups.
26 Windows tests and 16 Linux API/public-release checks passed. Actual hosted
concurrent journeys, isolation, redeploy persistence, and isolated backup restore
passed. See DEPLOYMENT_VALIDATION.md and OPERATIONS.md for scope and limitations.
GitHub publication and video explanation remain next steps.

## Handoff and startup update — 2026-09-13

The local app is implemented; public deployment remains pending. Read
[HANDOFF.md](HANDOFF.md) for the current implementation, external model/data
locations, verification scope, startup configuration, and deployment planning gaps.

Added automatic Windows sign-in startup and a one-minute scheduled check for the
launcher, service-exit recovery, duplicate-launch protection, and a detached
double-click launcher. Recovery was verified by stopping the supervisor and both
services. API/dashboard health passed again during handoff preparation; both
model artifact pairs are present. This does not establish public availability.

No cloud resources, purchases, Git commits, remotes, or GitHub publication have
been created. The user will provide deployment instructions in a new chat.

## Original local release record — 2026-09-11

Implementation started 2026-09-11. The agreed plan is docs/PROJECT_PLAN.md.

- [x] Environment installed and verified.
- [x] Initial physics, dataset, fitting, and training implementation written.
- [x] Physics and baseline tests pass.
- [x] Both models trained and exports parity checked.
- [x] Held-out benchmark and uncertainty evaluation complete.
- [x] API, experiment persistence, and dashboard implemented.
- [x] End-to-end browser workflow verified and application displayed.
- [x] Launch instructions and portfolio documentation complete.

Decision: serve exported dense/ReLU weights through a shared NumPy runtime to avoid loading both heavy ML frameworks in the application. Training uses real PyTorch and TensorFlow models; each export must numerically agree with its native model before use. Framework comparisons distinguish training framework from serving runtime.

Decision: use log-rate split-conformal intervals with independent calibration data. These are marginal intervals under the simulated training distribution, not evidence of real-device or out-of-distribution coverage.

Validation: 22 tests passed, both framework exports passed native parity checks, and the independent data-directory reproduction produced identical dataset hashes and exported model arrays. Accuracy and interval coverage matched; compute times varied with system load. Ruff checks pass.

Current services: launch.py started the API on 127.0.0.1:8765 and dashboard on 127.0.0.1:8501. The browser is showing the real local application. No cloud resources or API keys are used.

Browser checks completed: custom generation, all three estimators, truth reveal, history/reopen, benchmark/stress views, Bloch-sphere time control, and experiment JSON download. Inspected the default narrow layout and a 1280px desktop layout; no browser console errors were recorded. The temporary viewport override is reset for handoff.

Local release complete. Deferred beyond this release: public hosting, Docker, baseline bootstrap intervals, hardware data, and an independently run remote CI installation.
