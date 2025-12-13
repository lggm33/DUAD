from flask import Blueprint, jsonify

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


