import pytest
from fastapi.testclient import TestClient

from qnd.api import create_app


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(tmp_path / "test.sqlite3", tmp_path / "models"))


def test_complete_baseline_flow_and_persistence(client, tmp_path):
    created = client.post("/experiments", json={"seed": 123, "label": "Test mystery"})
    assert created.status_code == 201
    ex = created.json()
    assert "truth" not in ex and "seed" not in ex
    assert "gamma1" not in str(ex)
    identifier = ex["id"]
    prediction = client.post(f"/experiments/{identifier}/diagnose/baseline")
    assert prediction.status_code == 200
    assert prediction.json()["converged"]
    assert "truth" not in prediction.json()
    fresh = TestClient(create_app(tmp_path / "test.sqlite3", tmp_path / "models"))
    restored = fresh.get(f"/experiments/{identifier}").json()
    assert restored["diagnoses"]["baseline"] == prediction.json()
    assert "truth" not in restored
    revealed = fresh.post(f"/experiments/{identifier}/reveal").json()
    assert revealed["truth"]["seed"] == 123
    assert fresh.get(f"/experiments/{identifier}").json()["revealed"]
    assert fresh.get("/experiments").json()[0]["id"] == identifier


@pytest.mark.parametrize(
    "payload",
    [
        {"shots": -1},
        {"shots": 2.5},
        {"mode": "bad"},
        {"mode": "custom"},
        {"gamma1": 0.1},
        {"seed": -1},
        {"unexpected": 1},
        {"label": "x" * 81},
        {"mode": "custom", "gamma1": -0.1, "gamma_phi": 0.01},
    ],
)
def test_invalid_requests(client, payload):
    assert client.post("/experiments", json=payload).status_code == 422


def test_missing_and_unsupported_models(client):
    assert client.get("/experiments/missing").status_code == 404
    ex = client.post("/experiments", json={"shots": 64}).json()
    assert client.post(f"/experiments/{ex['id']}/diagnose/torch").status_code == 422
    ex = client.post("/experiments", json={}).json()
    assert client.post(f"/experiments/{ex['id']}/diagnose/tensorflow").status_code == 503
    assert client.post(f"/experiments/{ex['id']}/diagnose/bogus").status_code == 422


def test_zero_noise_serialization(client):
    ex = client.post("/experiments", json={"mode": "custom", "gamma1": 0, "gamma_phi": 0}).json()
    truth = client.post(f"/experiments/{ex['id']}/reveal").json()["truth"]
    assert truth["t1_us"] is None and truth["t2_us"] is None
