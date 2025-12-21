from flask import Blueprint, request, jsonify, make_response, Response
from app.extensions import db
from app.domain.users.user_repository import UserRepository
from app.domain.auth.refresh_token_repository import RefreshTokenRepository
from app.domain.auth.auth_service import AuthService, AuthError, EmailAlreadyExistsError, InvalidCredentialsError
from app.utils.jwt_service import JwtService
from app.utils.password_hasher import PasswordHasher
from app.config import get_settings
from app.presentation.common.errors import error_response

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

def get_auth_service() -> AuthService:
    settings = get_settings()
    session = db.get_session()
    user_repo = UserRepository(session)
    refresh_token_repo = RefreshTokenRepository(session)
    password_hasher = PasswordHasher()
    jwt_service = JwtService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_token_expires=settings.jwt_access_token_expires
    )
    return AuthService(user_repo, refresh_token_repo, password_hasher, jwt_service)

@auth_bp.post("/register")
def register():
    data = request.get_json()
    if not data or "email" not in data or "password" not in data or "name" not in data:
        return error_response("VALIDATION_ERROR", "Email, password and name are required", status_code=400)

    auth_service = get_auth_service()
    try:
        tokens = auth_service.register(
            email=data["email"], 
            password=data["password"],
            name=data["name"],
            username=data.get("username")
        )
        return _build_auth_response(tokens, status_code=201)
    except EmailAlreadyExistsError as e:
        return error_response("EMAIL_ALREADY_EXISTS", str(e), status_code=409)
    except AuthError as e:
        return error_response("AUTH_ERROR", str(e), status_code=400)

@auth_bp.post("/login")
def login():
    data = request.get_json()
    if not data or "email" not in data or "password" not in data:
        return error_response("VALIDATION_ERROR", "Email and password are required", status_code=400)

    auth_service = get_auth_service()
    try:
        tokens = auth_service.login(data["email"], data["password"])
        return _build_auth_response(tokens, status_code=200)
    except InvalidCredentialsError as e:
        return error_response("INVALID_CREDENTIALS", str(e), status_code=401)
    except AuthError as e:
        return error_response("AUTH_ERROR", str(e), status_code=400)

def _build_auth_response(tokens: dict[str, str], status_code: int) -> Response:
    response = make_response(jsonify({"access_token": tokens["access_token"]}), status_code)
    
    # Secure cookie configuration following ADR-009
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=True,  # In production must be True, but for unified domain/reverse proxy it's safer
        samesite="Lax",
        path="/api/v1/auth"
    )
    return response
