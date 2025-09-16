# app/services/auth_service.py
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy.exc import SQLAlchemyError
from app.repos import user_repo
from app.utils.exceptions import (
    EmailInUseError,
    InvalidCredentialsError, 
    UserNotFoundError,
    RepoError,
    AppError
)

def register_user(email: str, password: str, name: str, phone: str = None, role: str = "customer"):
    # normalize input
    email = email.lower().strip()
    if user_repo.get_by_email(email):
        raise EmailInUseError()

    try:
        pwd_hash = generate_password_hash(password)
        user = user_repo.create_user(
            email=email, 
            password_hash=pwd_hash, 
            name=name,
            phone=phone,
            role=role
        )
        return user
    except user_repo.RepoError as e:
        # wrap lower-level errors
        raise AppError(f"Could not create user: {e}")

def authenticate_user(email: str, password: str):
    email = email.lower().strip()
    user = user_repo.get_by_email(email)
    if not user or not check_password_hash(user.password_hash, password):
        raise InvalidCredentialsError()
    return user

def issue_tokens_for(user):
    # attach role (and whatever else) as custom claims
    claims = {"role": user.role}
    return {
        "access_token": create_access_token(identity=str(user.id), additional_claims=claims),
        "refresh_token": create_refresh_token(identity=str(user.id)),
    }

def get_user_or_404(user_id: int):
    user = user_repo.get_by_id(user_id)
    if not user:
        raise UserNotFoundError()
    return user
