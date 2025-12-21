from app.domain.users.models import User, UserRole
from app.utils.password_hasher import PasswordHasher

def test_get_me_unauthorized(client, cleanup_database):
    # Act
    response = client.get("/api/v1/users/me")

    # Assert
    assert response.status_code == 401
    assert response.get_json()["code"] == "MISSING_AUTH_HEADER"

def test_get_me_success(client, session, cleanup_database):
    # 1. Create a user
    hasher = PasswordHasher()
    user = User(
        email="me_test@example.com", 
        password_hash=hasher.hash("pass123"), 
        name="Me Test User",
        username="metest",
        role=UserRole.USER.value
    )
    session.add(user)
    session.commit()
    
    # 2. Login to get a token
    login_data = {"email": "me_test@example.com", "password": "pass123"}
    login_resp = client.post("/api/v1/auth/login", json=login_data)
    access_token = login_resp.get_json()["access_token"]
    
    # 3. Access /me endpoint
    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"})

    # Assert
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == user.id
    assert data["email"] == "me_test@example.com"
    assert data["name"] == "Me Test User"
    assert data["username"] == "metest"
    assert data["role"] == UserRole.USER.value
    assert "password_hash" not in data
