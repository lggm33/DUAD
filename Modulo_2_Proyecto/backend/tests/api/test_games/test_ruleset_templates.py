"""
Tests for RulesetTemplate API endpoints.

Endpoints tested:
- GET /api/v1/ruleset-templates - List available templates
- GET /api/v1/ruleset-templates/<id> - Get template by ID
"""

import pytest
from app.domain.users.models import User, UserRole
from app.domain.games.ruleset_models import RulesetTemplate, RulesetSystemType
from app.utils.password_hasher import PasswordHasher


def create_test_user(session, email: str, name: str, username: str = None):
    """Helper to create a test user."""
    hasher = PasswordHasher()
    user = User(
        email=email,
        password_hash=hasher.hash("password123"),
        name=name,
        username=username or email.split("@")[0],
        role=UserRole.USER.value,
    )
    session.add(user)
    session.flush()
    return user


def get_auth_token(client, email: str, password: str = "password123"):
    """Helper to get authentication token."""
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    return login_resp.get_json()["access_token"]


def auth_headers(token: str):
    """Helper to create auth headers."""
    return {"Authorization": f"Bearer {token}"}


def create_ruleset_template(
    session,
    name: str,
    system_type: RulesetSystemType = RulesetSystemType.DND_5E,
    is_system_provided: bool = False,
    created_by_user_id: int = None,
):
    """Helper to create a ruleset template."""
    template = RulesetTemplate(
        name=name,
        description=f"Description for {name}",
        system_type=system_type,
        base_rules={"version": "1.0"},
        is_system_provided=is_system_provided,
        created_by_user_id=created_by_user_id,
    )
    session.add(template)
    session.flush()
    return template


class TestListRulesetTemplates:
    """Tests for GET /api/v1/ruleset-templates endpoint."""

    def test_list_templates_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.get("/api/v1/ruleset-templates")
        
        assert response.status_code == 401
        assert response.get_json()["code"] == "MISSING_AUTH_HEADER"

    def test_list_templates_empty(self, client, session, cleanup_database):
        """Test listing templates when none exist."""
        user = create_test_user(session, "test@example.com", "Test User")
        session.commit()
        
        token = get_auth_token(client, "test@example.com")
        response = client.get(
            "/api/v1/ruleset-templates", headers=auth_headers(token)
        )
        
        assert response.status_code == 200
        assert response.get_json() == []

    def test_list_templates_returns_system_templates(
        self, client, session, cleanup_database
    ):
        """Test that system templates are visible to all users."""
        user = create_test_user(session, "test@example.com", "Test User")
        
        template = create_ruleset_template(
            session,
            name="D&D 5e Standard",
            system_type=RulesetSystemType.DND_5E,
            is_system_provided=True,
        )
        session.commit()
        
        token = get_auth_token(client, "test@example.com")
        response = client.get(
            "/api/v1/ruleset-templates", headers=auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "D&D 5e Standard"
        assert data[0]["is_system_provided"] is True

    def test_list_templates_returns_user_templates(
        self, client, session, cleanup_database
    ):
        """Test that user can see their own custom templates."""
        user = create_test_user(session, "test@example.com", "Test User")
        
        template = create_ruleset_template(
            session,
            name="My Custom Rules",
            system_type=RulesetSystemType.CUSTOM,
            is_system_provided=False,
            created_by_user_id=user.id,
        )
        session.commit()
        
        token = get_auth_token(client, "test@example.com")
        response = client.get(
            "/api/v1/ruleset-templates", headers=auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "My Custom Rules"
        assert data[0]["created_by_user_id"] == user.id

    def test_list_templates_excludes_other_users_templates(
        self, client, session, cleanup_database
    ):
        """Test that user cannot see other users' custom templates."""
        user1 = create_test_user(session, "user1@example.com", "User 1", "user1")
        user2 = create_test_user(session, "user2@example.com", "User 2", "user2")
        
        template = create_ruleset_template(
            session,
            name="User2 Private Rules",
            system_type=RulesetSystemType.CUSTOM,
            is_system_provided=False,
            created_by_user_id=user2.id,
        )
        session.commit()
        
        token = get_auth_token(client, "user1@example.com")
        response = client.get(
            "/api/v1/ruleset-templates", headers=auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 0

    def test_list_templates_mixed_visibility(
        self, client, session, cleanup_database
    ):
        """Test listing with system templates and user's own templates."""
        user = create_test_user(session, "test@example.com", "Test User")
        other_user = create_test_user(
            session, "other@example.com", "Other User", "other"
        )
        
        system_template = create_ruleset_template(
            session,
            name="D&D 5e Standard",
            is_system_provided=True,
        )
        user_template = create_ruleset_template(
            session,
            name="My Rules",
            is_system_provided=False,
            created_by_user_id=user.id,
        )
        other_template = create_ruleset_template(
            session,
            name="Other User Rules",
            is_system_provided=False,
            created_by_user_id=other_user.id,
        )
        session.commit()
        
        token = get_auth_token(client, "test@example.com")
        response = client.get(
            "/api/v1/ruleset-templates", headers=auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        names = [t["name"] for t in data]
        assert "D&D 5e Standard" in names
        assert "My Rules" in names
        assert "Other User Rules" not in names


class TestGetRulesetTemplate:
    """Tests for GET /api/v1/ruleset-templates/<id> endpoint."""

    def test_get_template_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.get("/api/v1/ruleset-templates/1")
        
        assert response.status_code == 401

    def test_get_template_not_found(self, client, session, cleanup_database):
        """Test getting a non-existent template returns 404."""
        user = create_test_user(session, "test@example.com", "Test User")
        session.commit()
        
        token = get_auth_token(client, "test@example.com")
        response = client.get(
            "/api/v1/ruleset-templates/9999", headers=auth_headers(token)
        )
        
        assert response.status_code == 404
        assert response.get_json()["code"] == "TEMPLATE_NOT_FOUND"

    def test_get_system_template_success(self, client, session, cleanup_database):
        """Test getting a system template returns full details with base_rules."""
        user = create_test_user(session, "test@example.com", "Test User")
        template = create_ruleset_template(
            session,
            name="D&D 5e Standard",
            is_system_provided=True,
        )
        session.commit()
        
        token = get_auth_token(client, "test@example.com")
        response = client.get(
            f"/api/v1/ruleset-templates/{template.id}", headers=auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "D&D 5e Standard"
        assert data["is_system_provided"] is True
        assert "base_rules" in data
        assert data["base_rules"]["version"] == "1.0"

    def test_get_own_template_success(self, client, session, cleanup_database):
        """Test getting own custom template returns full details."""
        user = create_test_user(session, "test@example.com", "Test User")
        template = create_ruleset_template(
            session,
            name="My Custom Rules",
            is_system_provided=False,
            created_by_user_id=user.id,
        )
        session.commit()
        
        token = get_auth_token(client, "test@example.com")
        response = client.get(
            f"/api/v1/ruleset-templates/{template.id}", headers=auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "My Custom Rules"
        assert data["created_by_user_id"] == user.id
        assert "base_rules" in data

    def test_get_other_users_template_forbidden(
        self, client, session, cleanup_database
    ):
        """Test that accessing another user's template returns 403."""
        user1 = create_test_user(session, "user1@example.com", "User 1", "user1")
        user2 = create_test_user(session, "user2@example.com", "User 2", "user2")
        
        template = create_ruleset_template(
            session,
            name="User2 Private Rules",
            is_system_provided=False,
            created_by_user_id=user2.id,
        )
        session.commit()
        
        token = get_auth_token(client, "user1@example.com")
        response = client.get(
            f"/api/v1/ruleset-templates/{template.id}", headers=auth_headers(token)
        )
        
        assert response.status_code == 403
        assert response.get_json()["code"] == "FORBIDDEN"

