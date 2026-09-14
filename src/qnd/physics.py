"""Time in microseconds; rates in inverse microseconds. No quantum hardware required."""

import numpy as np

TIMES = np.linspace(0.0, 300.0, 64)
SHOTS = 256
PROTOCOL = "paired-decay-v1"


def probabilities(gamma1, gamma_phi, times=TIMES):
    """Return (..., 2, time) probabilities: excited population and X-plus measurement."""
    g1, gp = np.broadcast_arrays(np.asarray(gamma1, float), np.asarray(gamma_phi, float))
    times = np.asarray(times, float)
    if (
        not np.all(np.isfinite(g1))
        or not np.all(np.isfinite(gp))
        or np.any(g1 < 0)
        or np.any(gp < 0)
    ):
        raise ValueError("Noise rates must be finite and nonnegative.")
    if times.ndim != 1 or not np.all(np.isfinite(times)) or np.any(times < 0):
        raise ValueError("Times must be a finite nonnegative vector.")
    energy = np.exp(-g1[..., None] * times)
    coherence = (1 + np.exp(-(g1 / 2 + gp)[..., None] * times)) / 2
    return np.stack([energy, coherence], axis=-2)


def sample(gamma1, gamma_phi, *, shots=SHOTS, seed=0, times=TIMES):
    if not isinstance(shots, (int, np.integer)) or shots < 1:
        raise ValueError("Shots must be a positive integer.")
    return np.random.default_rng(seed).binomial(shots, probabilities(gamma1, gamma_phi, times))


def qutip_reference(gamma1, gamma_phi, times=TIMES):
    """Independent Lindblad evolution with explicit |0> ground / |1> excited convention."""
    import qutip as qt

    ground, excited = qt.basis(2, 0), qt.basis(2, 1)
    plus = (ground + excited).unit()
    collapse = [np.sqrt(gamma1) * ground * excited.dag(), np.sqrt(gamma_phi / 2) * qt.sigmaz()]
    out = []
    for initial, measurement in [(excited, excited.proj()), (plus, plus.proj())]:
        result = qt.mesolve(
            0 * qt.sigmaz(),
            initial.proj(),
            times,
            collapse,
            e_ops=[measurement],
            options={"atol": 1e-10, "rtol": 1e-9},
        )
        out.append(result.expect[0])
    return np.asarray(out)


def derived(rates):
    g1, gp = [float(v) for v in rates]
    return {
        "gamma1": g1,
        "gamma_phi": gp,
        "t1_us": 1 / g1 if g1 > 1e-12 else None,
        "tphi_us": 1 / gp if gp > 1e-12 else None,
        "t2_us": 1 / (g1 / 2 + gp) if g1 / 2 + gp > 1e-12 else None,
    }
