# Quantum Noise Detective: instructions for the next session

Read `docs/HANDOFF.md` first, then `README.md` and `docs/PROGRESS.md`. Read
`docs/PROJECT_PLAN.md` for scientific intent; it is the original plan and includes
proposals that differ from the final local implementation. Verify current code
and runtime state before relying on dated validation records.

## User and working style

- Sam is a beginner in Python and neural networks. Explain required user actions
  plainly and in enough detail to follow them.
- Work autonomously on authorized implementation, investigation, and testing.
  Ask only when a material preference, account action, or missing authorization
  prevents progress. Do not ask Sam to perform routine development checks.
- Preserve the Python-first project, real PyTorch and TensorFlow training,
  conventional baseline, and scientifically honest results. No Qiskit or
  real-hardware claims. Do not invent resume metrics.
- The next session's user message will specify deployment instructions. This
  handoff does not authorize purchases, account creation, deployment, or GitHub
  publication. The intended order is finish the product, deploy, then GitHub.

## Workspace care

- Windows/PowerShell; use the Python 3.12 environment documented in the handoff.
- Trained models and SQLite history are outside the checkout. Preserve them.
- A Windows scheduled task now supervises local startup. Inspect it before
  starting competing servers or stopping processes; it can restart them.
- Keep credentials out of source, logs, and chat. User handles sign-in and billing.
- Update the handoff when material implementation or deployment decisions change.
  Record what was actually verified separately from earlier evidence.
