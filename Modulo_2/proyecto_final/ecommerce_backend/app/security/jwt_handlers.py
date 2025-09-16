from flask import jsonify
from app.extensions import jwt
from app.utils.exceptions import json_error

@jwt.unauthorized_loader
def missing_token_callback(err_msg):
    # Missing or invalid Authorization header
    return json_error("Missing or invalid Authorization header", 401)

@jwt.invalid_token_loader
def invalid_token_callback(err_msg):
    # Invalid token
    return json_error("Invalid token", 422)

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return json_error("Token expired", 401)

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return json_error("Token has been revoked", 401)

# (Optional) if you use "fresh" tokens for sensitive operations:
@jwt.needs_fresh_token_loader
def needs_fresh_token_callback(jwt_header, jwt_payload):
    return json_error("Fresh token required", 401)
