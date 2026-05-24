import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from backend.domain.schemas.models import GenerateRequest, GenerateResponse, RefineRequest, RefineResponse
from backend.core.dependencies import get_redis_repo, get_crew_service
from backend.repositories.redis_repo import RedisRepository
from backend.services.crew_service import CrewService

router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
def generate_angles(
    request: GenerateRequest,
    repo: RedisRepository = Depends(get_redis_repo),
    crew_service: CrewService = Depends(get_crew_service)
):
    # Hash the notes to check for cached response
    notes_hash = hashlib.sha256(request.notes.encode('utf-8')).hexdigest()
    
    # 1. Check cache
    cached_data = repo.get_cache(notes_hash)
    if cached_data:
        remaining = repo.get_generations_remaining(request.session_id)
        return GenerateResponse(angles=cached_data["angles"], generations_remaining=remaining)

    # 2. Check rate limit
    remaining = repo.get_generations_remaining(request.session_id)
    if remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You have reached your limit of 3 free generations. Please upgrade to a lifetime pass."
        )

    # 3. Call CrewService
    try:
        angles = crew_service.generate_angles(request.notes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 4. Increment usage
    repo.increment_usage(request.session_id)
    new_remaining = max(0, remaining - 1)

    # 5. Cache result
    repo.set_cache(notes_hash, {"angles": [a.model_dump() for a in angles]})

    return GenerateResponse(angles=angles, generations_remaining=new_remaining)

@router.post("/refine", response_model=RefineResponse)
def refine_angle(
    request: RefineRequest,
    crew_service: CrewService = Depends(get_crew_service)
):
    try:
        refined_text = crew_service.refine_angle(request.original_text, request.refinement_type)
        return RefineResponse(refined_text=refined_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
