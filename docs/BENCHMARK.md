# Benchmark: initial local release

The machine-readable record is [BENCHMARK.json](BENCHMARK.json). The dashboard reads the live record from the configured data directory.

## Design

T1 is sampled independently log-uniformly from 10–100 µs and Tphi from 10–200 µs. Each configuration produces two arrays of 64 binomial counts at 256 shots per delay, spanning 0–300 µs. There are 6,000 training, 800 validation, 800 calibration, and 800 test configurations, generated with separate seeds. Preprocessing uses training data only. Validation loss selects checkpoints; the test set is not used for selection.

Analytic curves agree with independent QuTiP Lindblad evolution within 2e-7 absolute tolerance in four representative limiting/mixed cases. High-shot fitting recovers known rates within the tested relative tolerance. These checks establish correctness of this specific simulator, not fidelity to a physical device.

## Models and inference

Both neural models use dense layers 128 -> 128 -> 64 -> 2 with ReLU hidden activations. Inputs are standardized frequencies; targets are standardized log rates. The PyTorch run uses Adam with 1e-5 weight decay; TensorFlow uses Adam without weight decay. Framework initializers differ. This compares these two trained estimators, not the inherent quality of their frameworks.

Native/export parity was checked on 32 validation experiments before calibration. The service executes exported weights through NumPy to avoid loading both ML frameworks. Export errors, versions, architecture, training histories, seeds, and artifact/dataset hashes are recorded in metadata.

Initial training times, including framework import but excluding dataset generation: about 9.9 seconds for PyTorch and 19.4 seconds for TensorFlow in the warmed development environment. First-ever imports and installation may be much slower. Data generation took about 0.30 seconds and used approximately 2.3 MB of uncompressed arrays.

## Results

| Method | γ1 median relative error | γphi median relative error | Median warm inference | γ1 coverage | γphi coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Binomial fit | 1.07% | 7.20% | 14.88 ms | Not implemented | Not implemented |
| PyTorch-trained MLP | 2.20% | 7.34% | 0.070 ms | 91.75% | 88.00% |
| TensorFlow-trained MLP | 3.31% | 10.38% | 0.070 ms | 92.375% | 89.25% |

Conventional fitting gives the lowest median errors; neural inference trades accuracy for lower compute time. One conventional fit reported non-convergence. Its returned finite estimate is included in aggregate errors; the app flags unconverged estimates.

Timings use the same CPU and one BLAS thread, excluding HTTP, UI, training, and artifact loading. They are not native TensorFlow-versus-PyTorch runtime comparisons. The raw report includes p95 compute and artifact-load times.

## Uncertainty and stress tests

Split conformal calibration uses absolute residuals in log-rate space, a separate 800-experiment calibration set, and a finite-sample order-statistic correction. It targets 90% marginal coverage per rate under exchangeability with that distribution. It does not imply 90% simultaneous coverage, conditional coverage at every noise level, or a probability that a particular estimate is correct.

The observed test coverage differs from 90%; finite test/calibration samples and randomness matter. The raw JSON includes coverage by rate tertile and interval widths.

The stress suite includes 160 experiments per condition: 64 shots, longer T1/Tphi outside training, and symmetric 5% readout error absent from training. Stress-only code rescales 64-shot frequencies for evaluation; the production API rejects non-256-shot neural requests. No calibration guarantee is claimed for these shifted distributions.

## Limits

- One training seed per framework, one fixed schedule, one idealized noise model.
- Baseline bootstrap intervals and real-hardware validation are not included.
- There is no claim that ML is more accurate or that quantum hardware accelerates it.
- Quality near rate boundaries or under mismatched noise can degrade substantially.
- A fresh installation on another machine is left to the configured CI workflow; local verification used the installed project environment.

The pipeline was also reproduced in a separate data directory. Dataset hashes and exported model arrays matched exactly; accuracy/coverage matched while timings changed with load. See [VALIDATION.md](VALIDATION.md).
