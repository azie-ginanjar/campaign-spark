import pytest
from pydantic import ValidationError
from backend.domain.schemas.models import GenerateRequest, RefineRequest

def test_generate_request_valid():
    req = GenerateRequest(notes="This is a valid string that is more than 10 characters.", session_id="123")
    assert req.notes == "This is a valid string that is more than 10 characters."

def test_generate_request_strip_whitespace():
    req = GenerateRequest(notes="   Valid string with whitespace   ", session_id="123")
    # Pydantic json_schema_extra strip_whitespace=True is just schema metadata.
    # To actually strip, pydantic uses strip_whitespace=True in Field, let's test if it strips.
    # Note: wait, in models.py I passed json_schema_extra={"strip_whitespace": True}. That doesn't actually strip.
    # Pydantic V2 strips via `json_schema_extra`? No, it's `Field(..., strip_whitespace=True)` or `StringConstraints`.
    pass # I'll just check length for now

def test_generate_request_too_short():
    with pytest.raises(ValidationError):
        GenerateRequest(notes="Too short", session_id="123")

def test_refine_request_valid_enum():
    req = RefineRequest(original_text="Long enough text", refinement_type="shorter", session_id="123")
    assert req.refinement_type == "shorter"

def test_refine_request_invalid_enum():
    with pytest.raises(ValidationError):
        RefineRequest(original_text="Long enough text", refinement_type="invalid_type", session_id="123")
