"""Run inside a serving container: API smoke test, restart persistence, backup/restore."""

import json
import os
import secrets
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx


def main():
    directory = Path(os.environ["QND_DATA_DIR"])
    evidence = directory / "release-validation.json"
    with httpx.Client(base_url="http://127.0.0.1:8765", timeout=30) as client:
        assert client.get("/ready").status_code == 200
        assert client.get("/experiments").status_code == 401

        def call(method, route, headers, **kwargs):
            for _ in range(10):
                response = client.request(method, route, headers=headers, **kwargs)
                if response.status_code != 429:
                    response.raise_for_status()
                    return response.json()
                time.sleep(0.5)
            raise RuntimeError("Demo remained busy during validation")

        if evidence.exists():
            visitors = json.loads(evidence.read_text())
            for item in visitors:
                ex = call("GET", f"/experiments/{item['id']}", item["headers"])
                assert len(ex["diagnoses"]) == 3 and ex["revealed"]
            print("Restart/redeploy persistence: PASS (5 visitors, 15 diagnoses)")
        else:
            def flow(index):
                headers = {"X-QND-Visitor": secrets.token_urlsafe(32)}
                ex = call("POST", "/experiments", headers,
                          json={"seed": 900 + index, "label": "Release validation"})
                assert "truth" not in ex
                for method in ("baseline", "torch", "tensorflow"):
                    result = call("POST", f"/experiments/{ex['id']}/diagnose/{method}", headers)
                    assert len(result["rates"]) == 2
                revealed = call("POST", f"/experiments/{ex['id']}/reveal", headers)
                assert "truth" in revealed
                assert len(call("GET", "/experiments", headers)) == 1
                return {"headers": headers, "id": ex["id"]}

            started = time.perf_counter()
            with ThreadPoolExecutor(max_workers=5) as pool:
                visitors = list(pool.map(flow, range(5)))
            evidence.write_text(json.dumps(visitors))
            evidence.chmod(0o600)
            print(f"Five simultaneous visitor journeys: PASS ({time.perf_counter()-started:.2f}s)")
        a, b = visitors[:2]
        for method, suffix in [("GET", ""), ("POST", "/reveal"),
                               ("POST", "/diagnose/baseline")]:
            assert client.request(method, f"/experiments/{a['id']}{suffix}",
                                  headers=b["headers"]).status_code == 404
        print("Cross-visitor access denial: PASS")
    backup = directory / "backups/release-validation.sqlite3"
    backup.parent.mkdir(exist_ok=True)
    with (sqlite3.connect(directory / "experiments.sqlite3") as source,
          sqlite3.connect(backup) as destination):
        source.backup(destination)
    with sqlite3.connect(backup) as source, sqlite3.connect(":memory:") as restored:
        source.backup(restored)
        assert restored.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert restored.execute("SELECT count(*) FROM diagnoses").fetchone()[0] >= 15
    print("SQLite-consistent backup and isolated restore: PASS")


if __name__ == "__main__":
    main()
