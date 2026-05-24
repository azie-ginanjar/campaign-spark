import hmac
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.config import settings
from backend.core.dependencies import get_redis_repo, get_crew_service
from backend.domain.schemas.models import AngleOutput

client = TestClient(app, base_url="http://localhost")

class MockRedisRepo:
    def __init__(self):
        self.usage = 0
        self.premium = False
        self.cache = {}
        self.tokens = {}

    def get_generations_remaining(self, session_id):
        return max(0, 3 - self.usage)
        
    def increment_usage(self, session_id):
        self.usage += 1

    def get_cache(self, h):
        return self.cache.get(h)

    def set_cache(self, h, data):
        self.cache[h] = data

    def is_premium(self, email):
        return self.premium

    def set_premium(self, email):
        self.premium = True

    def store_magic_link(self, email):
        token = "mocked_token_123"
        self.tokens[token] = email
        return token

    def verify_magic_link(self, token):
        if token in self.tokens:
            email = self.tokens.pop(token)
            return email
        return None


class MockCrewService:
    def generate_angles(self, notes):
        return [
            AngleOutput(angle_type="Benefit-Driven", content="Benefit text"),
            AngleOutput(angle_type="Problem/Solution", content="Problem text"),
            AngleOutput(angle_type="FOMO/Urgency", content="FOMO text")
        ]
    
    def refine_angle(self, original_text, refinement_type):
        return f"Refined text ({refinement_type})"

@pytest.fixture
def override_deps():
    mock_repo = MockRedisRepo()
    mock_crew = MockCrewService()
    
    app.dependency_overrides[get_redis_repo] = lambda: mock_repo
    app.dependency_overrides[get_crew_service] = lambda: mock_crew
    yield mock_repo, mock_crew
    app.dependency_overrides.clear()

# --- GENERATE ENDPOINT TESTS ---

def test_generate_endpoint_success(override_deps):
    mock_repo, _ = override_deps
    
    response = client.post("/api/v1/generate", json={
        "notes": "Valid notes string over 10 chars",
        "session_id": "test_session"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["angles"]) == 3
    assert data["generations_remaining"] == 2
    assert mock_repo.usage == 1

def test_generate_endpoint_cache_hit(override_deps):
    mock_repo, _ = override_deps
    
    notes = "Valid notes string over 10 chars"
    h = hashlib.sha256(notes.encode('utf-8')).hexdigest()
    
    # Pre-seed cache
    mock_repo.set_cache(h, {
        "angles": [{"angle_type": "Cached", "content": "Cached string"}]
    })
    
    response = client.post("/api/v1/generate", json={
        "notes": notes,
        "session_id": "test_session"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["angles"][0]["angle_type"] == "Cached"
    # Usage should not increment on cache hit
    assert mock_repo.usage == 0
    assert data["generations_remaining"] == 3

def test_generate_endpoint_rate_limit(override_deps):
    mock_repo, _ = override_deps
    mock_repo.usage = 3 # Max limit reached
    
    response = client.post("/api/v1/generate", json={
        "notes": "Valid notes string over 10 chars",
        "session_id": "test_session"
    })
    
    assert response.status_code == 403
    assert "limit" in response.json()["detail"]

# --- REFINE ENDPOINT TESTS ---

def test_refine_endpoint_success(override_deps):
    response = client.post("/api/v1/refine", json={
        "original_text": "This is a long angle text",
        "refinement_type": "shorter",
        "session_id": "test_session"
    })
    
    assert response.status_code == 200
    assert response.json()["refined_text"] == "Refined text (shorter)"

def test_refine_endpoint_invalid_type(override_deps):
    response = client.post("/api/v1/refine", json={
        "original_text": "This is a long angle text",
        "refinement_type": "invalid_type",
        "session_id": "test_session"
    })
    # Pydantic should block invalid literal
    assert response.status_code == 422

# --- WEBHOOK ENDPOINT TESTS ---

def test_webhook_valid_signature(override_deps):
    mock_repo, _ = override_deps
    
    payload = {
        "meta": {
            "custom_data": {
                "email": "premium@example.com"
            }
        }
    }
    raw_body = json.dumps(payload).encode('utf-8')
    secret = settings.lemonsqueezy_webhook_secret.get_secret_value().encode('utf-8')
    signature = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
    
    response = client.post(
        "/api/v1/webhooks/lemonsqueezy", 
        content=raw_body,
        headers={"x-signature": signature}
    )
    
    assert response.status_code == 200
    assert mock_repo.premium is True

def test_webhook_invalid_signature(override_deps):
    raw_body = b'{"some": "data"}'
    
    response = client.post(
        "/api/v1/webhooks/lemonsqueezy", 
        content=raw_body,
        headers={"x-signature": "fake_bad_signature"}
    )
    
    assert response.status_code == 401

# --- AUTH ENDPOINT TESTS ---

def test_request_magic_link_not_premium(override_deps):
    mock_repo, _ = override_deps
    mock_repo.premium = False
    
    response = client.post("/api/v1/auth/request-magic-link", json={
        "email": "test@example.com"
    })
    
    assert response.status_code == 403

def test_request_magic_link_premium(override_deps):
    mock_repo, _ = override_deps
    mock_repo.premium = True
    
    response = client.post("/api/v1/auth/request-magic-link", json={
        "email": "premium@example.com"
    })
    
    assert response.status_code == 200
    assert "mocked_token_123" in mock_repo.tokens

def test_verify_magic_link_valid(override_deps):
    mock_repo, _ = override_deps
    mock_repo.tokens["mocked_token_123"] = "premium@example.com"
    
    response = client.get("/api/v1/auth/verify?token=mocked_token_123")
    
    assert response.status_code == 200
    assert "session_token" in response.cookies
    # Verify token was atomically deleted
    assert "mocked_token_123" not in mock_repo.tokens

def test_verify_magic_link_invalid(override_deps):
    response = client.get("/api/v1/auth/verify?token=fake_token")
    assert response.status_code == 401
