from flask import Blueprint, jsonify, g, request
from app.extensions import db
from app.domain.users.user_repository import UserRepository
from app.domain.users.user_service import UserService
from app.presentation.users.presenters import UserPresenter
from app.presentation.common.auth import auth_required
from app.presentation.common.errors import error_response
import re

user_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")

def get_user_service() -> UserService:
    session = db.get_session()
    user_repo = UserRepository(session)
    return UserService(user_repo)

@user_bp.get("/me")
@auth_required
def get_me():
    """
    Returns the current authenticated user's information.
    """
    user_service = get_user_service()
    user_id = g.auth_user.user_id
    
    user = user_service.get_user_by_id(user_id)
    if not user:
        return error_response("USER_NOT_FOUND", "User not found", status_code=404)
    
    return jsonify(UserPresenter.public(user)), 200

@user_bp.patch("/me")
@auth_required
def update_me():
    """
    Updates the current authenticated user's profile information.
    """
    user_service = get_user_service()
    user_id = g.auth_user.user_id
    
    data = request.get_json()
    if not data:
        return error_response("INVALID_REQUEST", "No data provided", status_code=400)
    
    name = data.get("name")
    username = data.get("username")
    email = data.get("email")
    
    # Basic email validation if provided
    if email:
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return error_response("INVALID_EMAIL", "Invalid email format", status_code=400)
            
    try:
        user = user_service.update_profile(
            user_id=user_id,
            name=name,
            username=username,
            email=email
        )
        
        if not user:
            return error_response("USER_NOT_FOUND", "User not found", status_code=404)
            
        db.get_session().commit()
        return jsonify(UserPresenter.public(user)), 200
        
    except ValueError as e:
        return error_response("CONFLICT", str(e), status_code=409)
    except Exception as e:
        db.get_session().rollback()
        return error_response("INTERNAL_ERROR", str(e), status_code=500)
