# app/repos/user_repo.py
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.user import User
from app.utils.exceptions import RepoError
from datetime import datetime

def get_by_id(user_id: int) -> Optional[User]:
    return db.session.get(User, user_id)

def get_by_email(email: str) -> Optional[User]:
    return User.query.filter_by(email=email).first()

def create_user(email: str, password_hash: str, name: str, phone: str = None, role: str = "customer") -> User:
    try:
        user = User(
            email=email, 
            password_hash=password_hash, 
            name=name,
            phone=phone,
            role=role
        )
        db.session.add(user)
        db.session.commit()
        return user
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RepoError(str(e))  # bubble up with a clean error

def update_user(user_id: int, data: dict) -> Optional[User]:
    user = get_by_id(user_id)
    if not user:
        return None
    user.name = data.get("name", user.name)
    user.phone = data.get("phone", user.phone)
    user.role = data.get("role", user.role)
    user.is_active = data.get("is_active", user.is_active)
    user.updated_at = datetime.now()
    db.session.commit()
    return user

def delete_user(user_id: int) -> Optional[User]:
    user = get_by_id(user_id)
    if not user:
        return None
    db.session.delete(user)
    user.deleted_at = datetime.now()
    db.session.commit()
    return user