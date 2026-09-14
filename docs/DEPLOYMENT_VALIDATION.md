# Public release validation — 2026-09-13

Local date 2026-09-13; hosting timestamps extend into 2026-09-14 UTC.

Live URL: https://quantum.samuelflynn.dev
Latest verified deployment: `850dbd1e-7bd2-4a3d-99a7-280dfdfdfecd` (SUCCESS).
This redeploys release `53b05eb6-3bc3-47eb-92df-3b27e4afdf29` from the staged
directory `C:\Users\sam\.quantum-noise-detective-release\20260913-2`.

## Checks actually performed

- Backed up the existing checkout, native/exported models and live SQLite
  database using SQLite's backup API before implementation.
- Original 22 tests passed before changes. Updated suite: 26 tests passed on
  the documented Windows Python 3.12 interpreter. Ruff passed.
- Clean Linux Docker build succeeded with pinned serving dependencies and a
  pinned Python base-image digest. `pip check` reported no broken requirements.
  No PyTorch/TensorFlow/QuTiP serving dependency was required.
- 16 API/public-release tests passed inside the Linux image. These cover actual
  model inference, ownership, missing models, invalid requests, rate limiting,
  expiry, migration of old records, simultaneous visitors and isolated restore.
- Container startup checked artifact hashes, database access and actual model
  predictions before starting the public UI. API /ready returned ready.
- Deliberately terminated the local container API: supervisor exited and
  Docker restart policy restored readiness. Restart count became 1 and the
  existing experiment remained. The Windows local supervisor was not stopped.
- Actual Railway server test completed five simultaneous visitor journeys,
  each with conventional, PyTorch and TensorFlow diagnoses and truth reveal.
  Cross-visitor get/reveal/diagnose attempts returned 404.
- Redeployed the hosted service and reran the same check: five records and all
  15 diagnoses were preserved. Anonymous browser credentials are not promised
  to survive reconnects; database persistence is distinct from session identity.
- Created a consistent hosted SQLite backup, restored it into an isolated
  database and checked integrity and diagnoses. Downloaded that snapshot to
  `C:\Users\sam\.quantum-noise-detective-backups\hosted-20260913.sqlite3`;
  local integrity check returned ok and contained at least 15 diagnoses.
- Cloudflare CNAME and TXT records saved. Railway verified ownership and
  reported a VALID certificate. Public DNS resolver 1.1.1.1 resolved the name.
- Real HTTPS browser session worked at the custom domain, including WebSocket
  interactions. A request from the Railway machine through public HTTPS returned
  200 for / and /_stcore/health. Local curl with freshly resolved DNS also returned
  200 with normal TLS validation. Windows' default resolver still had a stale
  negative response during these checks; no system DNS configuration was changed.
- Public /experiments served Streamlit HTML, not the private FastAPI JSON API.
  Only port 8080 is exposed; API binds loopback 8765 in the container.
- Browser: mystery welcome experiment, custom settings, named experiment,
  compare methods, truth reveal, JSON download, saved history and reopening,
  benchmark page and field guide loaded. Separate browser tabs had different
  histories; the second did not list the first's named experiment.
- Downloaded `experiment-1948331f.json` contained all three diagnoses, expected
  custom truth T1=50 us, and no visitor credential/owner fields.
- Visually inspected desktop layout at 1280 px; fixed header clearance and
  removed the hosted developer toolbar. Observed a narrow 693 px DOM with no
  document horizontal overflow. Requested 390 px viewport overrides did not
  reliably apply; do not claim an actual phone-width visual pass or device test.
  Temporary viewport overrides were reset. Final public browser error log was empty.
- Railway measured about 234 MB current RAM during testing, with maximum 1 GB
  memory and 1 vCPU configured. This is a brief test observation, not a sustained
  load benchmark, monthly forecast, or availability guarantee.
- Workspace usage alert $10 / hard limit $15 verified. Hobby active.

## Limitations and operations

The whole scientific training pipeline was not rerun; existing artifacts and
recorded scientific benchmarks were preserved. Serving integration was verified
in Linux, but clean Linux native training parity was not newly tested.

Hobby's UI says managed backups/PITR require Pro. API attempts to enable managed
backups were denied, so none were enabled. Daily SQLite snapshots are on the
same volume, with one separately downloaded recovery copy. No automatic
off-volume backup or independent external uptime monitor is configured.

This is a bounded public portfolio demo with anonymous session history, a single
instance, and brief downtime possible during redeployments. GitHub publication,
remote CI execution, and the full explanatory/video guide remain later steps.
See OPERATIONS.md for update, restore, cost and shutdown details.
