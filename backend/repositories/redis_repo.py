import json
import secrets
from redis import Redis

class RedisRepository:
    def __init__(self, client: Redis):
        self.client = client

    def get_generations_remaining(self, session_id: str) -> int:
        """Returns the remaining free generations. Default is 3."""
        key = f"session:{session_id}:generations"
        usage = self.client.get(key)
        if usage is None:
            return 3
        return max(0, 3 - int(usage))

    def increment_usage(self, session_id: str):
        """Atomically increments the usage counter for a session (30-day TTL)."""
        key = f"session:{session_id}:generations"
        pipe = self.client.pipeline()
        pipe.incr(key)
        pipe.expire(key, 30 * 24 * 60 * 60)  # 30 days TTL
        pipe.execute()

    def set_premium(self, email: str):
        """Marks a user as premium based on their email."""
        key = f"user:{email}:premium"
        self.client.set(key, "1")

    def is_premium(self, email: str) -> bool:
        """Checks if a user is a premium user."""
        key = f"user:{email}:premium"
        val = self.client.get(key)
        # Redis returns bytes — decode before comparing
        return val is not None and val.decode('utf-8') == "1"

    def store_magic_link(self, email: str) -> str:
        """Generates a secure token, stores it with 15m TTL, and returns the token."""
        token = secrets.token_urlsafe(32)
        key = f"token:{token}"
        self.client.setex(key, 900, email) # 900 seconds = 15 minutes
        return token

    def verify_magic_link(self, token: str) -> str | None:
        """Atomically retrieves the email and deletes the token (single-use)."""
        key = f"token:{token}"
        # Pipeline to get and delete atomically
        pipe = self.client.pipeline()
        pipe.get(key)
        pipe.delete(key)
        results = pipe.execute()
        
        email = results[0]
        return email if email else None

    def get_cache(self, request_hash: str) -> dict | None:
        """Retrieves cached identical generation requests."""
        key = f"cache:{request_hash}"
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def set_cache(self, request_hash: str, response_data: dict):
        """Stores the response data in cache with a 24-hour TTL."""
        key = f"cache:{request_hash}"
        self.client.setex(key, 24 * 60 * 60, json.dumps(response_data))
