import pytest
from unittest.mock import MagicMock, patch
from backend.services.crew_service import CrewService
from backend.domain.schemas.ai_schemas import CrewOutput
from backend.domain.schemas.models import AngleOutput

@pytest.fixture
def crew_service():
    return CrewService()

@patch('backend.services.crew_service.Crew')
def test_generate_angles(mock_crew_class, crew_service):
    # Setup mock
    mock_crew_instance = MagicMock()
    mock_result = MagicMock()
    
    # Mock the pydantic output of CrewAI
    mock_crew_output = CrewOutput(angles=[
        AngleOutput(angle_type="Benefit-Driven", content="Benefit text"),
        AngleOutput(angle_type="Problem/Solution", content="Problem text"),
        AngleOutput(angle_type="FOMO/Urgency", content="FOMO text")
    ])
    mock_result.pydantic = mock_crew_output
    mock_crew_instance.kickoff.return_value = mock_result
    
    mock_crew_class.return_value = mock_crew_instance
    
    # Execute
    result = crew_service.generate_angles("Mocked notes for a fake product")
    
    # Assert
    assert len(result) == 3
    assert result[0].angle_type == "Benefit-Driven"
    assert result[1].angle_type == "Problem/Solution"
    assert result[2].angle_type == "FOMO/Urgency"
    mock_crew_instance.kickoff.assert_called_once()

@patch('backend.services.crew_service.Crew')
def test_refine_angle(mock_crew_class, crew_service):
    # Setup mock
    mock_crew_instance = MagicMock()
    mock_result = MagicMock()
    mock_result.raw = '"Refined short text"'
    mock_crew_instance.kickoff.return_value = mock_result
    
    mock_crew_class.return_value = mock_crew_instance
    
    # Execute
    result = crew_service.refine_angle("Original long text", "shorter")
    
    # Assert
    assert result == "Refined short text"
    mock_crew_instance.kickoff.assert_called_once()
