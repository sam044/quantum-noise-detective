# Public deployment plan

Prepared 2026-09-13. Status: Railway and $10-15/month budget approved; deployed 2026-09-13. See OPERATIONS.md and DEPLOYMENT_VALIDATION.md for actual configuration, verified results, and backup limitations. Original planning assumptions follow.

## Objective and sequence

Finish and validate the existing Quantum Noise Detective application, then deploy a public portfolio demo. Afterwards, publish the GitHub repository and usage guide (user step 2), then prepare the detailed explanation and video walkthrough (step 3). Preserve the Python, Streamlit, FastAPI, SQLite, conventional fitting, and genuinely trained PyTorch/TensorFlow implementation.

## Verified during planning

- Read HANDOFF, AGENTS, PROJECT_PLAN, README, and PROGRESS; inspected API, storage, settings, dependency configuration, launcher, dashboard request handling, and estimator imports.
- Local API returned healthy version 0.1.0, paired-decay-v1, with both model pairs present; dashboard health returned ok. The Windows supervisor task was Running.
- Both NPZ exports are 103,316 bytes each. Native training artifacts and metadata also exist outside the checkout.
- Storage currently has no visitor ownership checks. API list/get/reveal/diagnose operations share one experiment collection.
- Dependencies currently combine development, training, and serving. The launcher targets local ports and browser startup.
- No Git commits exist. Docker was not found on PATH. Full tests, native parity, and visual checks were not rerun for planning; older results remain dated evidence.

## Recommended hosting and budget

Use Railway Hobby with one Linux container, one replica, and an attached persistent volume for SQLite. Public HTTPS serves Streamlit; FastAPI is reachable only over loopback within the container. A Linux process supervisor manages both processes and shutdown; readiness checks must cover API, dashboard, database, and actual model loading.

Railway can upload/build local source with `railway up`, so GitHub publication and a separate image registry are not prerequisites. Use a carefully staged deployment directory and upload exclusions to avoid uploading local history, datasets, credentials, or native training files. Docker image construction can happen on the provider; validate in a clean Linux environment before public launch.

Hobby has a $5/month minimum including $5 usage. Current listed usage rates: RAM $10/GB-month, CPU $20/vCPU-month, volume $0.15/GB-month, egress $0.05/GB. Recommend a provisional $10-15 monthly budget for this small demo, pending measured memory/CPU usage; this is an estimate, not a fixed quote. Configure spending alerts and an approved hard usage limit, explaining that hitting it can stop availability. Confirm current billing semantics at setup. Use the included Railway domain; a purchased domain is optional.

Sources checked for planning:
- https://docs.railway.com/pricing
- https://docs.railway.com/cli/up
- https://docs.railway.com/networking/public-networking
- https://docs.railway.com/volumes
- https://docs.railway.com/volumes/backups
- https://docs.railway.com/pricing/cost-control

## Implementation order and completion gates

1. **Preserve and establish a baseline.** Create a local source snapshot and consistent SQLite backup using its backup API; preserve external models/data. Run existing lint/tests with the documented Python 3.12 environment. Verify native/export parity where needed. Inspect the scheduled task before any local process changes.
2. **Finish the public visitor experience.** Retest generate, all three diagnoses, truth reveal, history, JSON export, model comparison, and field guide. Replace local-only failure instructions with helpful hosted errors. Check desktop/mobile layouts, loading states, unsupported shots, zero rates, and out-of-distribution warnings. Keep scientific claims and benchmark caveats accurate.
3. **Isolate visitors and bound usage.** Add unguessable anonymous visitor credentials and enforce ownership in the API for every list/get/reveal/diagnose/export path; filtering the dashboard alone is insufficient. Proposed first release: history belongs to the active browser session, with clear notice that a new session may lose access and JSON is the durable user export. Persist records across service restarts but do not promise recovery of anonymous identity after a restart. Retain demo records for at most 7 days, cap experiments per session, bound total database growth and concurrent fits, and throttle repeated actions. Final numeric limits depend on load tests. Keep the API private and test cross-visitor access denials. Public storage starts empty; local history stays local.
4. **Package reproducible serving.** Split and pin Linux Python 3.12 serving dependencies from offline training/test dependencies; declare pandas explicitly. Package the two NPZ/JSON pairs and recorded benchmark with checksums/version manifest. Separate immutable models from the writable SQLite volume so mounting storage cannot hide models. Add Dockerfile, upload/build exclusions, Linux startup/shutdown handling, readiness, stdout logging, and configuration documentation. Training remains offline; never run it during requests or ordinary redeployments.
5. **Validate the release environment.** Run clean Linux installation/build, model-load/inference checks, API integration tests, and two independent browser sessions. Test isolation, quota behavior, export contents, database persistence, service failure/recovery, and a missing/corrupt model. Exercise roughly 5 simultaneous visitors initially; measure memory, CPU, latency and failures before choosing resource limits. This establishes a small-demo capacity, not an unlimited-user claim.
6. **Configure and deploy after account/budget decision.** Sam completes hosting sign-in and billing; agent prepares configuration and uploads the reviewed release. Configure region, HTTPS domain, Streamlit websocket behavior, persistent disk, environment values, restart policy, readiness, spending controls, and daily backups. Keep a single database-writing service replica. Expect brief maintenance downtime on volume-backed redeployments; do not claim zero downtime.
7. **Prove public operation and recovery.** Test the HTTPS URL from outside localhost, with desktop and mobile-sized browsers. Repeat the full user journey and independent visitor test. Verify the API is not publicly exposed, models/benchmark are available, and database records survive restart/redeploy. Make a SQLite-consistent backup, restore into an isolated database, and test it. Record resource usage, expected bill, actual test results, and the release version. Provide update, rollback, backup/restore, and shutdown instructions. Configure external uptime checking if available within the approved budget and notification preferences.

## User actions

- Decide whether the proposed $10-15/month paid-hosting budget is acceptable or whether hosting must be free.
- After provider selection, create/sign into Railway and complete any verification/payment setup personally. Authorize the deployment tool through its browser login when prompted; do not paste passwords or payment details into chat.
- No domain purchase, ML/API subscription, database account, or public GitHub repository is required for this proposed route.
- Technical implementation, packaging, routine validation, and deployment configuration are agent work. If account verification, a local installer/reboot, or another user-only step is necessary, explain the exact action at that time.

## Deployment is complete when

A public HTTPS URL runs independently of Sam's computer; all three estimators and the complete visitor flow work; visitors cannot access each other's records; persistence, restore and redeploy have been tested; resource limits and costs are understood; and the operational guide and handoff reflect measured results. Hosting work does not imply that GitHub publication or the video explanation has already been completed.
