# app/security/blocklist.py
import time
from app.extensions import cache

PREFIX = "blocklist:"

def block_token(jti: str, exp_unix: int):
    """Save the JTI until its expiration to block it."""
    ttl = max(0, exp_unix - int(time.time()))
    cache.set(f"{PREFIX}{jti}", "1", timeout=ttl)

def is_token_blocked(jti: str) -> bool:
    return cache.get(f"{PREFIX}{jti}") is not None
