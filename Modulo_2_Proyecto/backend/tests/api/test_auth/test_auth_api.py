import pytest
from flask import Flask
from app.domain.users.models import User, UserRole
from app.extensions import db

def test_register_success(client, session):
    """Test successful user registration."""
    data = {
        "email": "newuser@example.com",
        "password": "securepassword123",
        "name": "New User",
        "username": "newuser_1"
    }
    
    response = client.post("/api/v1/auth/register", json=data)
    
    assert response.status_code == 201
    assert "access_token" in response.get_json()
    
    # Verify refresh token cookie
    cookies = response.headers.getlist("Set-Cookie")
    assert any("refresh_token=" in c for c in cookies)
    assert any("HttpOnly" in c for c in cookies)
    assert any("Path=/api/v1/auth" in c for c in cookies)

    # Verify user was created in DB
    user = session.query(User).filter_by(email="newuser@example.com").first()
    assert user is not None
    assert user.email == "newuser@example.com"
    assert user.name == "New User"
    assert user.username == "newuser_1"

def test_register_duplicate_email(client, session):
    """Test registration with an already existing email."""
    # Create an initial user
    from app.utils.password_hasher import PasswordHasher
    hasher = PasswordHasher()
    user = User(
        email="existing@example.com", 
        password_hash=hasher.hash("pass"), 
        name="Existing",
        role=UserRole.USER.value
    )
    session.add(user)
    session.commit()

    data = {
        "email": "existing@example.com",
        "password": "password123",
        "name": "Another Name"
    }
    
    response = client.post("/api/v1/auth/register", json=data)
    
    assert response.status_code == 409
    json_data = response.get_json()
    assert json_data["code"] == "EMAIL_ALREADY_EXISTS"

def test_login_success(client, session):
    """Test successful user login."""
    from app.utils.password_hasher import PasswordHasher
    hasher = PasswordHasher()
    user = User(
        email="login@example.com", 
        password_hash=hasher.hash("correctpassword"), 
        name="Login User",
        role=UserRole.USER.value
    )
    session.add(user)
    session.commit()

    data = {
        "email": "login@example.com",
        "password": "correctpassword"
    }
    
    response = client.post("/api/v1/auth/login", json=data)
    
    assert response.status_code == 200
    assert "access_token" in response.get_json()
    
    # Verify refresh token cookie
    cookies = response.headers.getlist("Set-Cookie")
    assert any("refresh_token=" in c for c in cookies)

def test_login_invalid_credentials(client, session):
    """Test login with wrong password."""
    from app.utils.password_hasher import PasswordHasher
    hasher = PasswordHasher()
    user = User(
        email="wrongpass@example.com", 
        password_hash=hasher.hash("correctpassword"), 
        name="Wrong Pass User",
        role=UserRole.USER.value
    )
    session.add(user)
    session.commit()

    data = {
        "email": "wrongpass@example.com",
        "password": "wrongpassword"
    }
    
    response = client.post("/api/v1/auth/login", json=data)
    
    assert response.status_code == 401
    json_data = response.get_json()
    assert json_data["code"] == "INVALID_CREDENTIALS"

def test_register_missing_fields(client):
    """Test registration with missing fields."""
    response = client.post("/api/v1/auth/register", json={"email": "onlyemail@example.com", "password": "pass"})
    assert response.status_code == 400
    assert response.get_json()["code"] == "VALIDATION_ERROR"
    assert "name" in response.get_json()["message"].lower()

def test_register_malformed_json(client):
    """Test registration with malformed JSON."""
    response = client.post(
        "/api/v1/auth/register", 
        data='{"email": "test@example.com", "password": "pass" "name": "Test"}', # Missing comma
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data["code"] == "BAD_REQUEST"
    assert "Invalid request body or malformed JSON" in json_data["message"]
    # Ensure it's not the default HTML error
    assert response.is_json
