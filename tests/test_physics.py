import numpy as np
import pytest

from qnd.dataset import generate_split
from qnd.estimators import fit_baseline
from qnd.physics import TIMES, probabilities, qutip_reference, sample


@pytest.mark.parametrize("g1,gp", [(0, 0), (0.02, 0), (0, 0.03), (0.025, 0.0125)])
def test_lindblad_matches_analytic(g1, gp):
    np.testing.assert_allclose(qutip_reference(g1, gp), probabilities(g1, gp), atol=2e-7)


def test_limits_and_measurement_semantics():
    np.testing.assert_equal(probabilities(0, 0), np.ones((2, 64)))
    p = probabilities(0.1, 0.1)
    assert p[0, -1] < 1e-10
    assert abs(p[1, -1] - 0.5) < 1e-10
    c = sample(0.02, 0.01, seed=42)
    np.testing.assert_equal(c, sample(0.02, 0.01, seed=42))
    assert np.all(c[:, 0] == 256)
    assert np.all((c >= 0) & (c <= 256))
    assert len(TIMES) == 64


def test_high_shot_baseline_recovers_rates():
    truth = np.array([0.025, 0.0125])
    counts = sample(*truth, shots=100000, seed=7)
    estimate, success, _ = fit_baseline(counts, 100000)
    assert success
    np.testing.assert_allclose(estimate, truth, rtol=0.025)


def test_different_split_seeds_have_no_duplicate_configurations():
    a, y = generate_split(100, 10)
    b, z = generate_split(100, 11)
    assert not set(map(tuple, y)) & set(map(tuple, z))
    np.testing.assert_equal(a, generate_split(100, 10)[0])
    assert not np.array_equal(a, b)


def test_bad_physics_input():
    with pytest.raises(ValueError):
        probabilities(-0.1, 0.1)
