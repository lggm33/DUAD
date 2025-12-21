from flask import Blueprint, jsonify, g
from app.presentation.common.auth import auth_required

from app.extensions import db, redis_client


health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    checks = {
        "db": "unknown",
        "redis": "unknown",
    }

    try:
        db.ping()
        checks["db"] = "ok"
    except Exception:
        checks["db"] = "error"

    try:
        redis_client.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    return jsonify({"status": "ok", "checks": checks})


@health_bp.get("/health/protected")
@auth_required
def protected_health_check():
    return jsonify({
        "status": "ok",
        "message": "You are authenticated",
        "auth_user": {
            "user_id": g.auth_user.user_id,
            "role": g.auth_user.role
        }
    }), 200

