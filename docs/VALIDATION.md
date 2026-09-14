# Validation record

Local verification on 2026-09-11, Windows / Python 3.12.4.

## Scientific and application checks

- 22 pytest tests passed with both trained models present.
- QuTiP/analytic agreement checked for zero noise, relaxation only, pure dephasing only, and mixed noise.
- High-shot fitting recovery, finite count bounds, seed determinism, and disjoint latent configurations checked.
- API validation, missing IDs/models, unsupported neural shot counts, zero-rate serialization, hidden truth, reveal, and SQLite persistence checked.
- Each actual trained model exercised through the API; positive finite outputs, interval ordering, exact model-version recording, and saved diagnosis round-trip checked.
- Native-to-export predictions agreed at rtol 2e-5 / atol 1e-7 on 32 validation configurations for each framework.
- Ruff lint and formatting checks passed.

## Reproduction

Ran scripts/reproduce.py in a separate data directory using the existing Python environment. This regenerated the dataset, retrained both frameworks, recalibrated intervals, reevaluated the frozen test/stress sets, and passed all 22 tests.

Compared the results with the original run: dataset SHA-256 matched exactly, and every exported weight, bias, normalization array, and calibration quantile was array-equal for both models. Accuracy and coverage results matched. Timing varied with machine load: baseline median compute was about 14.88 ms initially versus 5.15 ms in reproduction, illustrating why latency claims must include run context.

This is data/model reproduction in one installed environment, not an independent clean-machine installation. The included GitHub Actions workflow is prepared for that installation check but has not run remotely.

## Browser verification

The working application was opened in the Codex browser. Verified generation of a new custom experiment, all three diagnoses, truth reveal, benchmark/stress view, saved-experiment history and reopen, the experiment JSON download event, and the Field guide's interactive time slider and rendered Bloch sphere. Both the default narrow layout and 1280px desktop layout were inspected. No browser console errors were recorded. The viewport override is reset for handoff.

## Non-blocking warnings

QuTiP notes that optional Matplotlib graphics are unavailable; numerical tests pass and the dashboard uses Plotly. The installed Starlette test client emits HTTPX/AnyIO deprecation warnings. TensorFlow reports native-Windows GPU execution is unavailable; this release intentionally uses CPU execution.
