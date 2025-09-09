# app/security/rbac.py (o auth_utils.py)
import time
from flask_jwt_extended import JWTManager
from app.extensions import cache  # si configuraste Redis como backend
from flask import current_app

# clave en Redis: blocklist:{jti} -> exp_unix
BLOCKLIST_PREFIX = "blocklist:"

def block_token(jti: str, expires_at: int):
    ttl = max(0, expires_at - int(time.time()))
    cache.set(f"{BLOCKLIST_PREFIX}{jti}", "1", timeout=ttl)

def is_token_blocked(jti: str) -> bool:
    return cache.get(f"{BLOCKLIST_PREFIX}{jti}") is not None
