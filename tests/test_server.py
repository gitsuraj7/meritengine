"""
tests/test_server.py — Integration tests for the FastAPI MeritEngine server.
"""

import json
from pathlib import Path
from fastapi.testclient import TestClient

from meritengine.api.server import app

client = TestClient(app)
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "meritengine"}


def test_evaluate_endpoint():
    candidate_data = load_fixture("candidate_promising.json")
    role_data = load_fixture("role_backend_senior.json")

    payload = {
        "candidate": candidate_data,
        "role": role_data
    }

    response = client.post("/evaluate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["candidate_id"] == "promising-001"
    assert data["verdict"] in ("hire", "strong_hire")
    assert "Priya Sharma" in data["human_review_notes"]


def test_rank_endpoint():
    polished_data = load_fixture("candidate_polished.json")
    promising_data = load_fixture("candidate_promising.json")
    role_data = load_fixture("role_backend_senior.json")

    payload = {
        "candidates": [polished_data, promising_data],
        "role": role_data
    }

    response = client.post("/rank", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["total_evaluated"] == 2
    assert len(data["candidates"]) == 2
    
    # Priority order: Priya (#1) then Arjun (#2)
    assert data["candidates"][0]["verdict"]["candidate_id"] == "promising-001"
    assert data["candidates"][0]["rank"] == 1
    
    assert data["candidates"][1]["verdict"]["candidate_id"] == "polished-001"
    assert data["candidates"][1]["rank"] == 2
