import os
import json
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Any, Dict, List

app = FastAPI(title="Mock ATS Server (Company Side)")

# In-memory store for received webhook results
received_candidates: List[Dict[str, Any]] = []

@app.post("/webhook/meritengine_results", tags=["Webhook"])
async def receive_meritengine_results(request: Request):
    """
    Receives final verdicts and rankings from MeritEngine.
    """
    data = await request.json()
    # If it's a single candidate or batch, we append to our store
    if isinstance(data, list):
        received_candidates.extend(data)
    else:
        received_candidates.append(data)
        
    return {"status": "success", "message": "Results received by ATS."}

@app.get("/api/candidates", tags=["API"])
def get_candidates():
    """
    Returns all candidates received from MeritEngine for the UI.
    """
    return {"candidates": received_candidates}

@app.post("/api/reset", tags=["API"])
def reset_ats():
    """
    Clears the ATS database for demo purposes.
    """
    received_candidates.clear()
    return {"status": "reset"}

# ---------------------------------------------------------
# UI MOUNT
# ---------------------------------------------------------

ui_dir = os.path.join(os.path.dirname(__file__), "ui")
os.makedirs(ui_dir, exist_ok=True)

# Create index.html if it doesn't exist
index_path = os.path.join(ui_dir, "index.html")
if not os.path.exists(index_path):
    with open(index_path, "w") as f:
        f.write("<h1>Mock ATS Loading...</h1>")

app.mount("/", StaticFiles(directory=ui_dir, html=True), name="ats_ui")

if __name__ == "__main__":
    import uvicorn
    # Run the mock ATS on port 8001
    uvicorn.run("meritengine.mock_ats.server:app", host="0.0.0.0", port=8001, reload=True)
