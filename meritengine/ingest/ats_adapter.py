from typing import Any, Dict
from pydantic import ValidationError

try:
    from fastapi import HTTPException
except ImportError:
    # Fallback if FastAPI is not installed, though it's likely used if we need to return HTTP 400.
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
            super().__init__(f"{status_code} Bad Request: {detail}")

from meritengine.core.models import Candidate

def parse_ats_payload(payload: Dict[str, Any]) -> Candidate:
    """
    Takes a raw ATS webhook payload (Greenhouse-style or generic flat JSON)
    and maps it to the internal Candidate model.
    Unknown fields are ignored. 
    Missing required fields raise a 400 with a clear error message.
    """
    
    # Extract ID - look for generic or ATS-specific id fields
    candidate_id = payload.get("id") or payload.get("candidate_id") or payload.get("application_id")
    
    # Extract Name - can be single field or first/last split
    name = payload.get("name")
    if not name:
        first_name = payload.get("first_name", "")
        last_name = payload.get("last_name", "")
        if first_name or last_name:
            name = f"{first_name} {last_name}".strip()
            
    # Required field validation
    missing_fields = []
    if not candidate_id:
        missing_fields.append("id (or candidate_id/application_id)")
    if not name:
        missing_fields.append("name (or first_name/last_name)")
        
    if missing_fields:
        raise HTTPException(
            status_code=400, 
            detail=f"Missing required fields to create a Candidate: {', '.join(missing_fields)}"
        )

    # Extract Email (handles flat JSON and Greenhouse-style nested objects)
    email = payload.get("email", "")
    if not email and "email_addresses" in payload and isinstance(payload["email_addresses"], list):
        if len(payload["email_addresses"]) > 0:
            email_obj = payload["email_addresses"][0]
            if isinstance(email_obj, dict):
                email = email_obj.get("value", "")
            else:
                email = str(email_obj)
                
    # Extract Location
    location = payload.get("location", "")
    if not location and "location" in payload and isinstance(payload["location"], dict):
        location = payload["location"].get("name", "")

    # Extract standard fields gracefully
    bio = payload.get("bio", "")
    resume_text = payload.get("resume_text", "")
    current_ctc = payload.get("current_ctc")
    expected_ctc = payload.get("expected_ctc")
    notice_period_days = payload.get("notice_period_days")
    willing_to_relocate = payload.get("willing_to_relocate", False)
    skills_claimed = payload.get("skills_claimed", [])
    
    # Extract complex/nested arrays if provided
    # (Leaving these out of payload dict.get for brevity, but they could be mapped here too)
    
    try:
        candidate = Candidate(
            id=str(candidate_id),
            name=str(name),
            email=str(email),
            bio=str(bio),
            resume_text=str(resume_text),
            current_ctc=float(current_ctc) if current_ctc is not None else None,
            expected_ctc=float(expected_ctc) if expected_ctc is not None else None,
            notice_period_days=int(notice_period_days) if notice_period_days is not None else None,
            location=str(location),
            willing_to_relocate=bool(willing_to_relocate),
            skills_claimed=skills_claimed if isinstance(skills_claimed, list) else []
        )
        return candidate
    except ValidationError as e:
        # Catch pydantic type validation issues
        raise HTTPException(
            status_code=400, 
            detail=f"Data type validation error when mapping payload to Candidate: {str(e)}"
        )
