from typing import List, Literal
from pydantic import BaseModel, Field

class GenerateRequest(BaseModel):
    notes: str = Field(
        ..., 
        min_length=10, 
        max_length=5000, 
        description="Raw product notes or ideas",
        json_schema_extra={"strip_whitespace": True}
    )
    session_id: str = Field(..., min_length=1, description="Unique identifier for the user session")

class AngleOutput(BaseModel):
    angle_type: str  # e.g., "Benefit-Driven", "Problem/Solution", "FOMO/Urgency"
    content: str

class GenerateResponse(BaseModel):
    angles: List[AngleOutput]
    generations_remaining: int

class RefineRequest(BaseModel):
    original_text: str = Field(..., min_length=5, description="The text of the angle to refine")
    refinement_type: Literal['shorter', 'casual'] = Field(..., description="Type of refinement to apply")
    session_id: str = Field(..., min_length=1)

class RefineResponse(BaseModel):
    refined_text: str
