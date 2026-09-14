"""Integration checks against actual trained artifacts; skipped on a source-only checkout."""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from qnd.api import create_app
from qnd.estimators import PortableMLP
from qnd.settings import data_dir, model_dir


@pytest.mark.parametrize("method", ["torch", "tensorflow"])
def test_trained_model_end_to_end(method, tmp_path):
    path = model_dir() / f"{method}.npz"
    if not path.exists():
        pytest.skip("Run offline training to enable trained-artifact integration tests.")
    model = PortableMLP(path)
    with np.load(data_dir() / "dataset.npz") as data:
        counts = data["test_counts"][:32]
    rates = model.predict(counts)
    assert rates.shape == (32, 2)
    assert np.all(np.isfinite(rates)) and np.all(rates > 0)
    intervals = model.intervals(rates)
    assert np.all(intervals[:, :, 0] < rates)
    assert np.all(intervals[:, :, 1] > rates)
    assert model.metadata["export_max_absolute_error"] < 1e-6
    client = TestClient(create_app(tmp_path / "model.sqlite3", model_dir()))
    ex = client.post("/experiments", json={"seed": 909}).json()
    response = client.post(f"/experiments/{ex['id']}/diagnose/{method}")
    assert response.status_code == 200
    result = response.json()
    np.testing.assert_allclose(result["rates"], model.predict(ex["counts"])[0])
    assert result["model_version"] == model.metadata["model_version"]
    assert "truth" not in result
    assert client.get(f"/experiments/{ex['id']}").json()["diagnoses"][method] == result
