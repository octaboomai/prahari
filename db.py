import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

DB_PATH = Path(os.environ.get("PRAHARI_DB_PATH", str(Path(__file__).resolve().parent.parent / "prahari.db")))
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema.sql"


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    # Seed a default org profile row if none exists yet, so the app is usable
    # immediately without a separate onboarding step.
    row = conn.execute("SELECT id FROM org_profile WHERE id = 1").fetchone()
    if row is None:
        conn.execute(
            """INSERT INTO org_profile
               (id, org_name, sector, address, poc_name, poc_role, poc_contact, poc_email,
                dpo_name, dpo_contact, dpo_email)
               VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "Your Company Pvt Ltd", "Manufacturing", "",
                "", "IT / Security Lead", "", "",
                "", "", "",
            ),
        )
    conn.commit()
    conn.close()


# ---------- org profile ----------

def get_org_profile():
    conn = get_conn()
    row = conn.execute("SELECT * FROM org_profile WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else None


def update_org_profile(fields: dict):
    conn = get_conn()
    cols = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(f"UPDATE org_profile SET {cols} WHERE id = 1", list(fields.values()))
    conn.commit()
    conn.close()


# ---------- incidents ----------

def create_incident(data: dict) -> int:
    data = dict(data)
    data["incident_types"] = json.dumps(data.get("incident_types", []))
    data["created_at"] = datetime.now().isoformat(timespec="seconds")
    cols = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    conn = get_conn()
    cur = conn.execute(
        f"INSERT INTO incidents ({cols}) VALUES ({placeholders})",
        list(data.values()),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def get_incident(incident_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    incident = dict(row)
    incident["incident_types"] = json.loads(incident["incident_types"] or "[]")
    return incident


def list_incidents(include_closed: bool = True):
    conn = get_conn()
    q = "SELECT * FROM incidents ORDER BY detection_datetime DESC"
    rows = conn.execute(q).fetchall()
    conn.close()
    incidents = []
    for row in rows:
        incident = dict(row)
        incident["incident_types"] = json.loads(incident["incident_types"] or "[]")
        if not include_closed and incident["status"] == "closed":
            continue
        incidents.append(incident)
    return incidents


def mark_reported(incident_id: int, field: str):
    """field is one of: cert_in_reported_at, dpdp_initial_reported_at, dpdp_detailed_reported_at"""
    assert field in ("cert_in_reported_at", "dpdp_initial_reported_at", "dpdp_detailed_reported_at")
    conn = get_conn()
    conn.execute(
        f"UPDATE incidents SET {field} = ? WHERE id = ?",
        (datetime.now().isoformat(timespec="seconds"), incident_id),
    )
    incident = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    incident = dict(incident)
    if incident["cert_in_reported_at"] and incident["dpdp_detailed_reported_at"]:
        new_status = "fully_reported"
    elif incident["cert_in_reported_at"] or incident["dpdp_initial_reported_at"] or incident["dpdp_detailed_reported_at"]:
        new_status = "partially_reported"
    else:
        new_status = "open"
    conn.execute("UPDATE incidents SET status = ? WHERE id = ?", (new_status, incident_id))
    conn.commit()
    conn.close()


def close_incident(incident_id: int):
    conn = get_conn()
    conn.execute("UPDATE incidents SET status = 'closed' WHERE id = ?", (incident_id,))
    conn.commit()
    conn.close()


# ---------- log sources (retention tracking) ----------

def create_log_source(name: str, monitoring_start_date: str, notes: str = ""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO log_sources (name, monitoring_start_date, notes) VALUES (?, ?, ?)",
        (name, monitoring_start_date, notes),
    )
    conn.commit()
    conn.close()


def list_log_sources():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM log_sources ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_log_source(source_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM log_sources WHERE id = ?", (source_id,))
    conn.commit()
    conn.close()
