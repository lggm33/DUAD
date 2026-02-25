from typing import Any, Optional
from flask import jsonify, Response

def error_response(code: str, message: str, details: Optional[Any] = None, status_code: int = 400) -> Response:
    """
    Returns a consistent error response as defined in the API Contract.
    """
    payload = {
        "code": code,
        "message": message,
        "details": details
    }
    return jsonify(payload), status_code
