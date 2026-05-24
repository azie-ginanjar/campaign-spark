import redis
from fastapi import Depends
from .config import settings
from backend.repositories.redis_repo import RedisRepository

def get_redis_client():
    r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield r
    finally:
        r.close()

def get_redis_repo(client: redis.Redis = Depends(get_redis_client)) -> RedisRepository:
    return RedisRepository(client)

def get_crew_service() -> "CrewService":
    from backend.services.crew_service import CrewService
    return CrewService()
