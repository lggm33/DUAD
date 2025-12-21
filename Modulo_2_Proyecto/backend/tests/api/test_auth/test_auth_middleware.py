import pytest
from app.domain.users.models import User, UserRole
from app.utils.password_hasher import PasswordHasher

def test_protected_route_no_header(client):
    """Test protected route without Authorization header."""
    response = client.get("/api/v1/health/protected")
    assert response.status_code == 401
    assert response.get_json()["code"] == "MISSING_AUTH_HEADER"

def test_protected_route_invalid_header_format(client):
    """Test protected route with invalid Authorization header format."""
    response = client.get("/api/v1/health/protected", headers={"Authorization": "InvalidFormat token"})
    assert response.status_code == 401
    assert response.get_json()["code"] == "INVALID_AUTH_HEADER"

def test_protected_route_invalid_token(client):
    """Test protected route with invalid token."""
    response = client.get("/api/v1/health/protected", headers={"Authorization": "Bearer invalid.token.here"})
    assert response.status_code == 401
    assert response.get_json()["code"] == "INVALID_TOKEN"

def test_protected_route_success(client, session):
    """Test protected route with valid token."""
    # 1. Create a user
    hasher = PasswordHasher()
    user = User(
        email="middleware_test@example.com", 
        password_hash=hasher.hash("pass123"), 
        name="Middleware Test User",
        role=UserRole.USER.value
    )
    session.add(user)
    session.commit()
    
    # 2. Login to get a token
    login_data = {"email": "middleware_test@example.com", "password": "pass123"}
    login_resp = client.post("/api/v1/auth/login", json=login_data)
    access_token = login_resp.get_json()["access_token"]
    
    # 3. Access protected route
    response = client.get("/api/v1/health/protected", headers={"Authorization": f"Bearer {access_token}"})
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "ok"
    assert json_data["auth_user"]["user_id"] == user.id
    assert json_data["auth_user"]["role"] == UserRole.USER.value

def test_protected_route_expired_token(client, session, monkeypatch):
    """Test protected route with expired token."""
    # 1. Create a user
    hasher = PasswordHasher()
    user = User(
        email="expired@example.com", 
        password_hash=hasher.hash("pass123"), 
        name="Expired User",
        role=UserRole.USER.value
    )
    session.add(user)
    session.commit()
    
    # 2. Login to get a token
    login_data = {"email": "expired@example.com", "password": "pass123"}
    login_resp = client.post("/api/v1/auth/login", json=login_data)
    access_token = login_resp.get_json()["access_token"]
    
    # 3. Simulate expiration by mocking JwtService.verify to raise JwtExpiredError
    from app.utils.jwt_service import JwtExpiredError, JwtService
    def mock_verify(*args, **kwargs):
        raise JwtExpiredError("Token has expired")
    
    monkeypatch.setattr(JwtService, "verify", mock_verify)
    
    # 4. Access protected route
    response = client.get("/api/v1/health/protected", headers={"Authorization": f"Bearer {access_token}"})
    
    assert response.status_code == 401
    assert response.get_json()["code"] == "TOKEN_EXPIRED"
