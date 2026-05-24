import fakeredis
import pytest
from backend.repositories.redis_repo import RedisRepository

@pytest.fixture
def repo():
    client = fakeredis.FakeRedis(decode_responses=True)
    return RedisRepository(client)

def test_generations_remaining_default(repo):
    assert repo.get_generations_remaining("test_session") == 3

def test_increment_usage_and_remaining(repo):
    repo.increment_usage("test_session")
    assert repo.get_generations_remaining("test_session") == 2
    repo.increment_usage("test_session")
    assert repo.get_generations_remaining("test_session") == 1
    repo.increment_usage("test_session")
    assert repo.get_generations_remaining("test_session") == 0
    # Even if used 4 times, remaining shouldn't be negative
    repo.increment_usage("test_session")
    assert repo.get_generations_remaining("test_session") == 0

def test_premium_status(repo):
    assert not repo.is_premium("test@example.com")
    repo.set_premium("test@example.com")
    assert repo.is_premium("test@example.com")

def test_magic_link_atomic_single_use(repo):
    token = repo.store_magic_link("test@example.com")
    assert token is not None
    
    # First verification should return email
    email = repo.verify_magic_link(token)
    assert email == "test@example.com"
    
    # Second verification should return None (atomically deleted)
    email2 = repo.verify_magic_link(token)
    assert email2 is None
