from flask import Blueprint, jsonify, g
from app.extensions import db
from app.domain.users.user_repository import UserRepository
from app.domain.users.user_service import UserService
from app.presentation.users.presenters import UserPresenter
from app.presentation.common.auth import auth_required
from app.presentation.common.errors import error_response

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
