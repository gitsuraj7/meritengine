import sqlite3
import os
from pathlib import Path
from typing import Optional

from meritengine.core.models import Candidate, RoleSpec, CandidateVerdict

# Data directory relative to this file
DB_PATH = Path(__file__).parent.parent / "data" / "meritengine.db"

def get_connection():
    """Returns a SQLite connection. Creates the data directory if it doesn't exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(DB_PATH))

def init_db():
    """Initializes the candidate_pipeline_state table."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS candidate_pipeline_state (
                candidate_id TEXT PRIMARY KEY,
                webhook_url TEXT,
                status TEXT,
                candidate_json TEXT,
                role_json TEXT,
                verdict_json TEXT
            )
        """)
        conn.commit()

def reset_db():
    """Drops the table and reinitializes. Used for demo resets."""
    with get_connection() as conn:
        conn.execute("DROP TABLE IF EXISTS candidate_pipeline_state")
    init_db()

def add_to_supervisor_queue(candidate: Candidate, role: RoleSpec, webhook_url: str):
    """Adds a candidate to the pending_supervisor queue."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO candidate_pipeline_state 
            (candidate_id, webhook_url, status, candidate_json, role_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(candidate_id) DO UPDATE SET
            webhook_url = excluded.webhook_url,
            status = excluded.status,
            candidate_json = excluded.candidate_json,
            role_json = excluded.role_json
        """, (
            candidate.id, 
            webhook_url, 
            "pending_supervisor", 
            candidate.model_dump_json(), 
            role.model_dump_json()
        ))

def get_supervisor_queue() -> list[tuple[Candidate, RoleSpec, str]]:
    """Retrieves all pending candidates."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT candidate_json, role_json, webhook_url 
            FROM candidate_pipeline_state 
            WHERE status = 'pending_supervisor'
        """)
        results = []
        for row in cursor.fetchall():
            c = Candidate.model_validate_json(row[0])
            r = RoleSpec.model_validate_json(row[1])
            webhook = row[2]
            results.append((c, r, webhook))
        return results

def get_pending_candidate(candidate_id: str) -> Optional[tuple[Candidate, RoleSpec, str]]:
    """Retrieves a specific pending candidate."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT candidate_json, role_json, webhook_url 
            FROM candidate_pipeline_state 
            WHERE candidate_id = ? AND status = 'pending_supervisor'
        """, (candidate_id,))
        row = cursor.fetchone()
        if row:
            c = Candidate.model_validate_json(row[0])
            r = RoleSpec.model_validate_json(row[1])
            webhook = row[2]
            return (c, r, webhook)
        return None

def update_candidate_status(candidate_id: str, status: str):
    """Updates the status of a candidate (e.g., to 'approved_for_battle')."""
    with get_connection() as conn:
        conn.execute("""
            UPDATE candidate_pipeline_state
            SET status = ?
            WHERE candidate_id = ?
        """, (status, candidate_id))

def save_final_verdict(candidate_id: str, verdict: CandidateVerdict):
    """Saves the final CandidateVerdict and marks status as finished."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO candidate_pipeline_state 
            (candidate_id, status, verdict_json)
            VALUES (?, ?, ?)
            ON CONFLICT(candidate_id) DO UPDATE SET
            status = excluded.status,
            verdict_json = excluded.verdict_json
        """, (candidate_id, "finished", verdict.model_dump_json()))

def save_batch_final_verdicts(verdicts: list[CandidateVerdict]):
    """Bulk saves final verdicts for performance."""
    with get_connection() as conn:
        data = [
            (v.candidate_id, "finished", v.model_dump_json())
            for v in verdicts
        ]
        conn.executemany("""
            INSERT INTO candidate_pipeline_state 
            (candidate_id, status, verdict_json)
            VALUES (?, ?, ?)
            ON CONFLICT(candidate_id) DO UPDATE SET
            status = excluded.status,
            verdict_json = excluded.verdict_json
        """, data)

def get_approved_for_battle() -> list[tuple[Candidate, RoleSpec]]:
    """Retrieves all candidates that have been approved by supervisor or pipeline for L2."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT candidate_json, role_json 
            FROM candidate_pipeline_state 
            WHERE status = 'approved_for_battle'
        """)
        results = []
        for row in cursor.fetchall():
            c = Candidate.model_validate_json(row[0])
            r = RoleSpec.model_validate_json(row[1])
            results.append((c, r))
        return results

def get_all_finished_verdicts() -> list[CandidateVerdict]:
    """Retrieves all finished verdicts from the DB."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT verdict_json 
            FROM candidate_pipeline_state 
            WHERE status = 'finished' AND verdict_json IS NOT NULL
        """)
        results = []
        for row in cursor.fetchall():
            results.append(CandidateVerdict.model_validate_json(row[0]))
        return results
