"""Small SQLite repository; measurement payloads and hidden truth are stored separately."""

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4


class CapacityError(Exception):
    pass


class Repository:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY, created TEXT NOT NULL, label TEXT NOT NULL,
                measurements TEXT NOT NULL, truth TEXT NOT NULL,
                revealed INTEGER NOT NULL DEFAULT 0)""")
            db.execute("""CREATE TABLE IF NOT EXISTS diagnoses (
                experiment_id TEXT NOT NULL REFERENCES experiments(id), method TEXT NOT NULL,
                payload TEXT NOT NULL, PRIMARY KEY(experiment_id, method))""")
            columns = {r[1] for r in db.execute("PRAGMA table_info(experiments)")}
            if "owner" not in columns:
                db.execute("ALTER TABLE experiments ADD COLUMN owner TEXT NOT NULL DEFAULT 'local'")
            db.execute("CREATE INDEX IF NOT EXISTS experiments_owner ON experiments(owner)")
            db.execute("CREATE INDEX IF NOT EXISTS experiments_created ON experiments(created)")

    def connect(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def create(self, label, measurements, truth, owner="local", bounded=False):
        identifier = str(uuid4())
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if bounded:
                total = db.execute("SELECT count(*) FROM experiments").fetchone()[0]
                owned = db.execute(
                    "SELECT count(*) FROM experiments WHERE owner=?", (owner,)
                ).fetchone()[0]
                if total >= 10000 or owned >= 100:
                    raise CapacityError("Demo storage limit reached. Download existing results.")
            db.execute(
                """INSERT INTO experiments
                (id,created,label,measurements,truth,revealed,owner) VALUES (?, ?, ?, ?, ?, 0, ?)""",
                (
                    identifier,
                    datetime.now(UTC).isoformat(),
                    label,
                    json.dumps(measurements),
                    json.dumps(truth),
                    owner,
                ),
            )
        return self.get(identifier, owner)

    def get(self, identifier, owner="local"):
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM experiments WHERE id=? AND owner=?", (identifier, owner)
            ).fetchone()
            if row is None:
                raise KeyError(identifier)
            diagnoses = db.execute(
                "SELECT method,payload FROM diagnoses WHERE experiment_id=?", (identifier,)
            ).fetchall()
        result = {
            "id": row["id"],
            "created": row["created"],
            "label": row["label"],
            **json.loads(row["measurements"]),
            "revealed": bool(row["revealed"]),
            "diagnoses": {r["method"]: json.loads(r["payload"]) for r in diagnoses},
        }
        if row["revealed"]:
            result["truth"] = json.loads(row["truth"])
        return result

    def reveal(self, identifier, owner="local"):
        self.get(identifier, owner)
        with self.connect() as db:
            db.execute(
                "UPDATE experiments SET revealed=1 WHERE id=? AND owner=?", (identifier, owner)
            )
        return self.get(identifier, owner)

    def save_diagnosis(self, identifier, method, payload, owner="local"):
        self.get(identifier, owner)
        with self.connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO diagnoses VALUES (?, ?, ?)",
                (identifier, method, json.dumps(payload)),
            )

    def list(self, owner="local"):
        with self.connect() as db:
            rows = db.execute("""SELECT id,created,label,revealed FROM experiments WHERE owner=?
                                 ORDER BY created DESC LIMIT 100""", (owner,)).fetchall()
        return [dict(r) for r in rows]

    def prune(self):
        cutoff = (datetime.now(UTC) - timedelta(days=7)).isoformat()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""DELETE FROM diagnoses WHERE experiment_id IN
                       (SELECT id FROM experiments WHERE created<? AND owner!='local')""",
                       (cutoff,))
            db.execute("DELETE FROM experiments WHERE created<? AND owner!='local'", (cutoff,))
