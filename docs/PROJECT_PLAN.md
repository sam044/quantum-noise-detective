# Project plan

> Historical planning document. For the implemented local release, later decisions,
> and the next deployment phase, read [HANDOFF.md](HANDOFF.md) and
> [PROGRESS.md](PROGRESS.md). Proposed features below are not all implemented.

## Product and audience

Build a local interactive lab that answers: "Given repeated measurements of a simulated qubit, how quickly is it losing energy and coherence, and how certain are those estimates?"

The portfolio should demonstrate numerical correctness, reproducible ML, backend development, persistence, and clear visual communication. A recruiter should understand the demo quickly; a technical interviewer should be able to inspect the experimental design and benchmarks.

## First-release scope

- One qubit with time-independent energy relaxation and pure dephasing.
- Two complementary measurement protocols, fixed known time grids, and finite measurement counts.
- Two inferred parameters: relaxation rate gamma1 and pure-dephasing rate gamma_phi.
- A conventional statistical estimator, a PyTorch estimator, and a TensorFlow/Keras comparison model.
- Calibrated uncertainty as a later milestone within the first release.
- A local Streamlit dashboard, FastAPI backend, and SQLite experiment history.
- Reproducible configurations, automated checks, and an honest benchmark report.

Exclude hardware integration, Qiskit, multi-qubit simulation, real-time device control, accounts, paid APIs, and online training from the initial release. Temperature effects, readout errors, drifting noise, and unknown frequency offsets are later robustness experiments.

## Physics and measurement design

Relaxation means an excited qubit loses energy. Pure dephasing means phase coherence decays without requiring an energy transition. Both contribute to the overall coherence decay.

Use nonnegative rates, in inverse microseconds:

- gamma1 = 1 / T1, where T1 is the energy-relaxation time.
- gamma_phi = 1 / Tphi, where Tphi is the pure-dephasing time.
- gamma2 = gamma1 / 2 + gamma_phi = 1 / T2.

The UI will show rates and derived times with units. Zero rates imply infinite characteristic times and must be represented explicitly rather than divided by zero. Positive rate constraints enforce T2 <= 2*T1 under this noise model.

Protocol A: prepare the excited state and measure excited-state population after a delay t. Under the initial zero-temperature model:

    P(excited | t) = exp(-gamma1 * t)

Protocol B: prepare the equal superposition |+>, evolve in a rotating frame with no detuning, and measure in the X basis:

    P(+ | t) = (1 + exp(-(gamma1 / 2 + gamma_phi) * t)) / 2

This is a simplified Ramsey-style coherence experiment. A population-decay curve alone cannot identify pure dephasing; the paired protocols are essential.

At every time point, prepare fresh copies of the state and sample counts from a binomial distribution. These curves are aggregated repeated experiments, not a continuously observed single qubit. Begin with ideal state preparation and readout.

Use QuTiP's Lindblad master-equation solver for a reference simulation. Verify basis conventions and collapse-operator scaling against the analytic curves before generating data. After agreement, use vectorized analytic probabilities to generate larger datasets cheaply, with sampled cross-checks against QuTiP.

Provisional experimental settings, to validate in milestone 1:

- T1 from 10 to 100 microseconds and Tphi from 10 to 200 microseconds, sampled through an explicitly documented distribution.
- 64 time points from 0 to 300 microseconds per protocol.
- 256 repeated measurements per time point initially.
- Separate robustness tests at lower/higher shot counts and outside the training parameter ranges.

If the measurement window is too short, too long, or too coarse to resolve a rate, the system should report weak evidence. A narrow-looking interval from an untested model must not imply physical certainty.

## Machine learning and baseline

Input: both observed count/frequency curves and their measurement metadata. Initially train for one fixed time grid and shot count; reject unsupported inputs until variable settings have been trained and evaluated explicitly. Simulator labels never enter the inference input.

Baseline: constrained SciPy nonlinear fitting for an initial reference, then a binomial maximum-likelihood fit for the main comparison. Use nonnegative rates and account for failed fits. Bootstrap measurement counts to estimate baseline uncertainty.

Main model: a small PyTorch multilayer perceptron predicting nonnegative rates. Start with compact layers suitable for CPU training. Add convolutional or larger sequence models only if evaluation justifies them.

TensorFlow/Keras: implement an equivalent small model against the same data, target transformations, and evaluation harness. Run frameworks sequentially and load only the selected inference model to limit RAM use. Framework comparison is secondary to scientific performance; using both is part of the requested learning scope.

Uncertainty: use an ensemble or quantile model, then a separate held-out calibration set to calibrate intervals. Report marginal interval coverage and width for each rate, including coverage across noise regimes. State the assumptions behind calibration; in-distribution coverage is not an out-of-distribution guarantee. Derived-time intervals need care near zero rate.

## Data and evaluation

1. Start with a 2,000-configuration pilot. Scale toward 20,000 only after timing and memory measurements.
2. Separate training, validation, calibration, and test configurations before producing repeated measurements. Never place different shot realizations of the same latent experiment in different splits.
3. Record units, noise parameters, time grid, shot counts, seeds, simulator version, dataset version, and source revision.
4. Fit preprocessing only on training data; tune on validation data and reserve calibration data for intervals.
5. Freeze the test set before reporting results. Add a separate stress suite for range shifts, shot-count shifts, and later model mismatch.

Metrics:

- Absolute error for each rate and median relative error away from zero.
- Error in derived T1/T2 when meaningful; do not let near-infinite times dominate summaries.
- Interval coverage and width by parameter regime.
- Baseline convergence/failure rates and invalid-input behavior.
- Warm single-experiment inference latency and cold model-load time measured separately on the same machine.
- Dataset-generation time, training time, and memory observations.

There is no predetermined claim that ML will beat fitting. An accurate, calibrated estimator with useful inference throughput would be a valid result; a strong conventional baseline is also an important finding. Published figures will include unfavorable cases.

## Architecture

    Streamlit interface -> FastAPI -> simulation / diagnosis services
                                  -> SQLite experiment metadata
                                  -> local array and model artifacts

Train offline through repeatable Python commands. The API loads saved model artifacts and never starts expensive training in a user request. No Redis, Kubernetes, or separate database server is necessary for the first local release.

Planned backend actions:

- Create an experiment from validated settings.
- Diagnose measurements with the chosen estimator.
- Reveal hidden ground truth through an explicit separate action.
- List and retrieve saved experiments and diagnoses.
- Report service readiness and loaded model version.

Keep hidden labels out of inference requests and initial demo responses. Bound time-point and shot-count requests. Persist configurations, seeds, artifact references, model versions, estimates, intervals, and timing measurements. Use a temporary SQLite database in persistence tests.

Proposed layout once implementation starts:

    src/quantum_noise_detective/
        physics/
        data/
        baselines/
        models/
        evaluation/
        api/
        storage/
    dashboard/
    configs/
    tests/
    docs/

Large generated datasets, virtual environments, and model artifacts stay out of Git. On this machine, keep heavy runtime files outside OneDrive where practical; configure their paths separately from source code.

## Milestones and completion criteria

1. Physics reference: paired noiseless curves and sampled counts; analytic/QuTiP agreement; correct zero-noise, relaxation-only, and dephasing-only limits; normalized states and valid probabilities.
2. Dataset and baseline: deterministic regeneration, recorded units/seeds, disjoint splits, and baseline recovery checks at high shot counts. Save baseline results before ML experiments.
3. ML estimators: CPU PyTorch training and equivalent TensorFlow run; saved artifacts; reproducible held-out accuracy and latency comparison.
4. Uncertainty and stress tests: calibrated intervals, regime-specific coverage, and a clear account of unsupported experiment settings and model mismatch.
5. Application: complete generate -> diagnose -> reveal -> save/reload flow; backend input checks, model-version tracking, and persistence tests.
6. Portfolio release: clean-environment reproduction, automated GitHub checks, benchmark report, short demo recording, architecture explanation, and measured resume bullets. Docker and hosting are optional follow-up work.

The user has no Python or neural-network experience and wants an agent-led prototype in 1-2 days. Implementation and technical investigation are the assistant's responsibility; explanations should assume no prior ML knowledge. The user does not need to complete a course before development starts.

Target a focused local prototype in 1-2 days, subject to installation, training, and debugging results. This is a target, not a guarantee or a commitment to complete every portfolio milestone in that window.

Day 1 priority: verified paired-protocol simulator, small deterministic dataset, conventional baseline, compact PyTorch estimator, and an initial end-to-end local demo.

Day 2 priority: TensorFlow comparison, dashboard polish, FastAPI integration, saved experiments, meaningful tests, and a concise benchmark/demo guide. Use serial runs and a small dataset on this laptop. If integration takes longer, finish the working core before adding optional features; do not claim missing features are complete.

Uncertainty intervals, their calibration and stress testing, Docker, hosted deployment, and broader portfolio polish follow the working prototype unless time permits. The demo should display that uncertainty is unavailable until it is implemented and evaluated; no fabricated confidence scores. Both ML frameworks remain in the intended release scope.

The six milestones above describe the complete portfolio release. The 1-2 day target describes the initial prototype. Milestone completion and measured evidence govern the release claims.

## Decisions already made and remaining

Decided: Python-first, PyTorch plus TensorFlow, local CPU execution, synthetic data, two measurement protocols, conventional baseline, no API keys, planning before application implementation.

Confirmed: beginner in Python and neural networks, agent-led development, desired prototype turnaround of 1-2 days. Default audience: general software and ML engineering recruiters. Further preference questions should not block ordinary technical decisions.

## References

- [QuTiP Lindblad solver documentation](https://qutip.readthedocs.io/en/stable/guide/dynamics/dynamics-master.html)
- [QuTiP project and installation](https://github.com/qutip/qutip)
- [PyTorch installation](https://pytorch.org/get-started/locally/)
- [TensorFlow installation and Windows limitations](https://www.tensorflow.org/install/pip)
