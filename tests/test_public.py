"""Public release boundaries: ownership, resource limits, expiry and recovery."""

import secrets
import sqlite3
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from qnd.api import create_app
from qnd.settings import model_dir
from qnd.storage import Repository


def visitor():
    return {"X-QND-Visitor": secrets.token_urlsafe(32)}


def test_public_ownership_and_restart(tmp_path):
    path = tmp_path / "history.sqlite3"
    app = create_app(path, model_dir(), public=True)
    a, b = visitor(), visitor()
    with TestClient(app) as client:
        assert client.post("/experiments", json={}).status_code == 401
        ex = client.post("/experiments", json={}, headers=a).json()
        identifier = ex["id"]
        assert "truth" not in ex and "owner" not in ex
        assert client.get("/experiments", headers=b).json() == []
        for method, route in [("GET", ""), ("POST", "/reveal"),
                              ("POST", "/diagnose/baseline"), ("POST", "/diagnose/torch"),
                              ("POST", "/diagnose/tensorflow")]:
            assert client.request(method, f"/experiments/{identifier}{route}",
                                  headers=b).status_code == 404
        for method in ("baseline", "torch", "tensorflow"):
            assert client.post(f"/experiments/{identifier}/diagnose/{method}",
                               headers=a).status_code == 200
        assert client.post(f"/experiments/{identifier}/reveal", headers=a).status_code == 200
    with TestClient(create_app(path, model_dir(), public=True)) as client:
        restored = client.get(f"/experiments/{identifier}", headers=a).json()
        assert restored["revealed"] and len(restored["diagnoses"]) == 3
        assert client.get(f"/experiments/{identifier}", headers=b).status_code == 404


def test_public_throttle_and_expiry(tmp_path):
    app = create_app(tmp_path / "history.sqlite3", model_dir(), public=True)
    a = visitor()
    with TestClient(app) as client:
        first = client.post("/experiments", headers=a, json={}).json()
        for _ in range(29):
            assert client.post("/experiments", headers=a, json={}).status_code == 201
        assert client.post("/experiments", headers=a, json={}).status_code == 429
        with app.state.repo.connect() as db:
            db.execute("UPDATE experiments SET created='2000-01-01' WHERE id=?", (first["id"],))
        items = client.get("/experiments", headers=a).json()
        assert len(items) == 29
        assert client.get(f"/experiments/{first['id']}", headers=a).status_code == 404


def test_legacy_migration_and_backup_restore(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("""CREATE TABLE experiments (id TEXT PRIMARY KEY, created TEXT NOT NULL,
                   label TEXT NOT NULL, measurements TEXT NOT NULL, truth TEXT NOT NULL,
                   revealed INTEGER NOT NULL DEFAULT 0)""")
        db.execute("INSERT INTO experiments VALUES ('old','2000-01-01','Saved','{}','{}',0)")
    repo = Repository(path)
    repo.prune()
    assert repo.get("old")["label"] == "Saved"
    assert repo.list("another-owner") == []
    restored = tmp_path / "restored.sqlite3"
    with repo.connect() as src, sqlite3.connect(restored) as dest:
        src.backup(dest)
        assert dest.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert Repository(restored).get("old") == repo.get("old")


def test_five_visitors_and_readiness(tmp_path):
    with TestClient(create_app(tmp_path / "load.sqlite3", model_dir(), public=True)) as client:
        assert client.get("/ready").status_code == 200

        def flow(_):
            headers = visitor()
            ex = client.post("/experiments", json={}, headers=headers).json()
            response = client.post(f"/experiments/{ex['id']}/diagnose/torch", headers=headers)
            assert response.status_code in (200, 429)
            assert len(client.get("/experiments", headers=headers).json()) == 1
            return ex["id"]

        with ThreadPoolExecutor(max_workers=5) as pool:
            assert len(set(pool.map(flow, range(5)))) == 5
    with TestClient(create_app(tmp_path / "missing.sqlite3", tmp_path / "missing")) as client:
        assert client.get("/ready").status_code == 503
