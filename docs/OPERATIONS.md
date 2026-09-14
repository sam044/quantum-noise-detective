# Hosting and recovery

Public URL: https://quantum.samuelflynn.dev

Railway project: `quantum-noise-detective`, service `quantum-lab`, production.
Project ID: `09f1f711-27bb-4207-a07c-4972e81458e5`.
Service ID: `7c94bc14-c989-4160-9395-1281958afb46`.
Environment ID: `aa279fca-6468-405c-b6c3-627ad2c28dbd`.
Volume ID: `bb53aa58-d5cc-4ee0-94b0-3d2ef67bcac5`, mounted at `/data`.

## What runs

One Linux container, one replica, US West, maximum 1 vCPU and 1 GB RAM.
The public port is 8080 (Streamlit); FastAPI listens only on 127.0.0.1:8765
inside the container. Railway terminates HTTPS. `scripts/serve.py` validates
artifact hashes, waits for API/database/model readiness, then starts Streamlit.
It exits on service failures or repeated unhealthy checks, allowing Railway's
restart policy to restart the container. Ten failure restarts are configured;
persistent failures need investigation. Volume-backed redeployments can cause
brief downtime and reset browser sessions.

`PORT=8080`, `QND_PUBLIC=1`, `QND_DATA_DIR=/data`, and
`QND_MODELS_DIR=/app/artifacts/models` are the hosted configuration.
Model exports and the benchmark are immutable image files, separate from the
database volume. No training frameworks are loaded during serving.

## Visitor behavior and limits

Each Streamlit session receives a random credential held only in server-side
session state. The API hashes it and enforces experiment ownership. A refresh,
reconnect or deployment may start a new session: this is not an account system.
JSON downloads let visitors keep their results. The database persists even if
the anonymous browser identity does not.

Limits: 100 experiments per session, 10,000 total, 30 write actions per visitor
per minute, 300 global write actions per minute, and two simultaneous diagnoses.
Previously saved diagnoses are reused. Expired public experiments are pruned
when the API handles authenticated experiment requests. Seven days is the
active-history lifetime; backup copies may retain older records for another
seven daily snapshots. Local-mode records retain their original behavior.

## Costs and accounts

Sam owns Railway billing and Cloudflare domain registration. Hobby is a $5/month
minimum including $5 usage; usage beyond that is billed separately. The workspace
has a $10 usage email alert and $15 hard usage limit. Hitting the hard limit can
stop the app. Taxes or registrar charges are separate. These are workspace-wide
settings: revisit them before adding another hosted project.

Cloudflare showed a $12.20/year domain renewal and active auto-renewal on
2026-09-13; future registry pricing can change. Only the `quantum` subdomain is
configured; the root and `www` remain available for a separate portfolio.

DNS in Cloudflare:
- CNAME `quantum` -> `rmn1y5xr.up.railway.app`, DNS only.
- TXT `_railway-verify.quantum` -> Railway's domain verification value.

The domain's HTTPS certificate is managed by Railway. Keep its verification
record. Check current domain details using `railway domain status quantum.samuelflynn.dev`.

## Checks and updates

Run commands from the checkout with the documented Python 3.12 environment.

```powershell
$labPython = 'C:\Users\sam\.venvs\quantum-noise-detective\Scripts\python.exe'
& $labPython -m pytest -q
& $labPython -m ruff check src tests dashboard scripts launch.py
docker build -t qnd:release .
railway status
railway logs --lines 100
railway metrics --cpu --memory --since 1h
railway usage
```

`scripts/stage_release.py <new-absolute-directory>` copies an explicit serving
allowlist, including checked model exports. It intentionally excludes local
history, native training artifacts, datasets, credentials, and repository-only
documentation. Stage to a NEW directory outside OneDrive; inspect it and use:

```powershell
railway up '<staged-directory>' --path-as-root --service quantum-lab --detach
railway deployment list --json
```

The Docker base image is pinned by digest and Linux serving dependencies are
pinned in `requirements-lock-linux-serving.txt`. Review and retest dependency
updates. `requirements-serving.txt` lists direct serving dependencies.
The platform configuration is set through `scripts/configure_host.graphql`;
the deprecated `railway.json` mechanism is not used.

To retest the CURRENT release without rebuilding:
`railway redeploy --service quantum-lab --yes`.
For a rollback, upload the previous retained release directory and validate
database compatibility first. Rolling code back does not reverse a schema
migration; restore a database only when necessary and after preserving the current one.

## Backup and restore

Hobby's UI explicitly restricts managed volume backups to Pro; none are enabled.
The app makes a SQLite-consistent daily backup under `/data/backups`, retaining
seven daily snapshots. It checks once per hour and backs up on the first ready
startup each UTC date. These copies protect against some application/data errors,
but sharing the same volume means they do not protect against losing the volume.

A separate tested copy was downloaded to
`C:\Users\sam\.quantum-noise-detective-backups\hosted-20260913.sqlite3`.
Download a fresh daily snapshot before significant updates, and periodically
if preserving demo history matters. There is no automatic off-volume backup job.

```powershell
railway volume files --volume bb53aa58-d5cc-4ee0-94b0-3d2ef67bcac5 list /backups --json
railway volume files --volume bb53aa58-d5cc-4ee0-94b0-3d2ef67bcac5 download /backups/<snapshot>.sqlite3 '<new-local-path>' --json
```

Restore procedure: preserve the current database with SQLite's backup API;
stop the hosted deployment so no writers remain; upload the chosen backup to
a temporary path on the volume; verify `PRAGMA integrity_check`; replace the
database while stopped and remove only its obsolete WAL/SHM companions; restart
and verify readiness, counts, and ownership. Never copy a live main database
alone and assume WAL data is included. The agent should perform these steps
with exact paths and a checked backup. The validation restored a backup into
an isolated database, not over the live production database.

## Operational access and stopping

The Railway CLI is signed in locally. A dedicated SSH key named
`qnd-railway-deployment` is registered; its private file is
`C:\Users\sam\.ssh\qnd_railway`, outside the checkout. Never publish it.
SSH host-key acceptance was completed through normal first-connection handling.
`scripts/check_host.py` can be piped to Python inside the container to verify
five visitor journeys, ownership, persistence, and backup/restore. Its private
validation session file stays on the volume and is not published.

If the app fails, inspect deployment logs and readiness first. Restart/redeploy
only the `quantum-lab` service. To stop hosting, remove the active deployment
through Railway's service controls; this is separate from cancelling the Hobby
subscription. Sam handles subscription cancellation. Keep/download the volume
before deleting cloud resources. Domain renewal is a separate Cloudflare setting.

Local Windows autostart remains independent of the public deployment. No local
supervisor task was disabled or reconfigured during this release.
