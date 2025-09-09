import app.repos.user_repo as user_repo
import app.services.delivery_address_service as delivery_address_service
from app.utils.exceptions import (
    UserNotFoundError,
    AppError,
    RepoError
)

def get_user_by_id(user_id: int):
    user = user_repo.get_by_id(user_id)
    if not user:  # If user NOT found
        raise UserNotFoundError()
    return user

def get_all_users():
    return user_repo.get_all()

def update_user(user_id: int, data: dict):
    updated_user = user_repo.update_user(user_id, data)
    if not updated_user:  # If update failed (user not found)
        raise UserNotFoundError()
    return updated_user

def delete_user(user_id: int):
    deleted_user = user_repo.delete_user(user_id)
    if not deleted_user:  # If delete failed (user not found)
        raise UserNotFoundError()
    return deleted_user