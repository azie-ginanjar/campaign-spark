from pydantic import BaseModel
from typing import List
from backend.domain.schemas.models import AngleOutput

class CrewOutput(BaseModel):
    angles: List[AngleOutput]
