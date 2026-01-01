"""
Tests for Game Rules API endpoints.

Endpoints tested:
- GET /api/v1/game/<id>/rules - Get effective rules for a game
- PUT /api/v1/game/<id>/rules - Update custom rules (DM only)
"""

import pytest
from app.domain.users.models import User, UserRole
from app.domain.games.models import (
    Game,
    GameStatus,
    GameMembership,
    GameRoleInGame,
    GameMembershipStatus,
)
from app.domain.games.ruleset_models import RulesetTemplate, RulesetSystemType
from app.utils.password_hasher import PasswordHasher


def create_test_user(
    session, email: str, name: str, username: str = None, role: str = UserRole.USER.value
):
    """Helper to create a test user."""
    hasher = PasswordHasher()
    user = User(
        email=email,
        password_hash=hasher.hash("password123"),
        name=name,
        username=username or email.split("@")[0],
        role=role,
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


def create_game_with_dm(
    session,
    dm_user: User,
    name: str = "Test Game",
    ruleset_template: RulesetTemplate = None,
    custom_rules: dict = None,
):
    """Helper to create a game with a DM membership."""
    game = Game(
        name=name,
        dm_user_id=dm_user.id,
        status=GameStatus.ACTIVE,
        ruleset_template_id=ruleset_template.id if ruleset_template else None,
        custom_rules=custom_rules,
    )
    session.add(game)
    session.flush()
    
    dm_membership = GameMembership(
        game_id=game.id,
        user_id=dm_user.id,
        role_in_game=GameRoleInGame.DM,
        status=GameMembershipStatus.ACTIVE,
    )
    session.add(dm_membership)
    session.flush()
    
    return game


def add_player_to_game(session, game: Game, player: User):
    """Helper to add a player to a game."""
    membership = GameMembership(
        game_id=game.id,
        user_id=player.id,
        role_in_game=GameRoleInGame.PLAYER,
        status=GameMembershipStatus.ACTIVE,
    )
    session.add(membership)
    session.flush()
    return membership


def create_ruleset_template(session, name: str = "D&D 5e"):
    """Helper to create a ruleset template with valid base rules."""
    template = RulesetTemplate(
        name=name,
        description="Standard rules",
        system_type=RulesetSystemType.DND_5E,
        base_rules={
            "version": "1.0",
            "character": {
                "creation_mode": "open",
                "level": {"min": 1, "max": 20, "default": 1},
            },
            "combat": {
                "turn_timeout": {
                    "enabled": True,
                    "grace_period_seconds": 60,
                    "max_wait_seconds": 180,
                    "default_action": "dodge",
                },
            },
        },
        is_system_provided=True,
    )
    session.add(template)
    session.flush()
    return template


class TestGetGameRules:
    """Tests for GET /api/v1/game/<id>/rules endpoint."""

    def test_get_rules_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.get("/api/v1/game/1/rules")
        
        assert response.status_code == 401

    def test_get_rules_game_not_found(self, client, session, cleanup_database):
        """Test getting rules for non-existent game returns 404."""
        user = create_test_user(session, "test@example.com", "Test User")
        session.commit()
        
        token = get_auth_token(client, "test@example.com")
        response = client.get(
            "/api/v1/game/9999/rules", headers=auth_headers(token)
        )
        
        assert response.status_code == 404
        assert response.get_json()["code"] == "GAME_NOT_FOUND"

    def test_get_rules_not_member(self, client, session, cleanup_database):
        """Test that non-member cannot access game rules."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        other_user = create_test_user(session, "other@example.com", "Other", "other")
        
        game = create_game_with_dm(session, dm)
        session.commit()
        
        token = get_auth_token(client, "other@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/rules", headers=auth_headers(token)
        )
        
        assert response.status_code == 403
        assert response.get_json()["code"] == "FORBIDDEN"

    def test_get_rules_no_template_no_custom(self, client, session, cleanup_database):
        """Test getting rules for game with no template and no custom rules."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()
        
        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/rules", headers=auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["game_id"] == game.id
        assert data["ruleset_template"] is None
        assert data["custom_rules"] is None
        assert data["effective_rules"] == {}

    def test_get_rules_with_template(self, client, session, cleanup_database):
        """Test getting rules for game with ruleset template."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        template = create_ruleset_template(session)
        game = create_game_with_dm(session, dm, ruleset_template=template)
        session.commit()
        
        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/rules", headers=auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["game_id"] == game.id
        assert data["ruleset_template"]["name"] == "D&D 5e"
        assert data["effective_rules"]["version"] == "1.0"
        assert "character" in data["effective_rules"]
        assert "combat" in data["effective_rules"]

    def test_get_rules_with_custom_overrides(self, client, session, cleanup_database):
        """Test getting rules with template and custom overrides."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        template = create_ruleset_template(session)
        custom_rules = {
            "character": {"level": {"default": 5}},
            "combat": {"turn_timeout": {"grace_period_seconds": 120}},
        }
        game = create_game_with_dm(
            session, dm, ruleset_template=template, custom_rules=custom_rules
        )
        session.commit()
        
        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/rules", headers=auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["custom_rules"] == custom_rules
        # Verify override was merged
        assert data["effective_rules"]["character"]["level"]["default"] == 5
        assert data["effective_rules"]["combat"]["turn_timeout"]["grace_period_seconds"] == 120
        # Verify non-overridden values remain
        assert data["effective_rules"]["character"]["level"]["max"] == 20

    def test_get_rules_as_player(self, client, session, cleanup_database):
        """Test that players can also view game rules."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")
        
        template = create_ruleset_template(session)
        game = create_game_with_dm(session, dm, ruleset_template=template)
        add_player_to_game(session, game, player)
        session.commit()
        
        token = get_auth_token(client, "player@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/rules", headers=auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["game_id"] == game.id
        assert data["ruleset_template"]["name"] == "D&D 5e"


class TestUpdateGameRules:
    """Tests for PUT /api/v1/game/<id>/rules endpoint."""

    def test_update_rules_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.put("/api/v1/game/1/rules", json={"custom_rules": {}})
        
        assert response.status_code == 401

    def test_update_rules_game_not_found(self, client, session, cleanup_database):
        """Test updating rules for non-existent game returns 404."""
        user = create_test_user(session, "test@example.com", "Test User")
        session.commit()
        
        token = get_auth_token(client, "test@example.com")
        response = client.put(
            "/api/v1/game/9999/rules",
            json={"custom_rules": {}},
            headers=auth_headers(token),
        )
        
        assert response.status_code == 404

    def test_update_rules_player_forbidden(self, client, session, cleanup_database):
        """Test that players cannot update game rules."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")
        
        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        session.commit()
        
        token = get_auth_token(client, "player@example.com")
        response = client.put(
            f"/api/v1/game/{game.id}/rules",
            json={"custom_rules": {"combat": {}}},
            headers=auth_headers(token),
        )
        
        assert response.status_code == 403
        assert response.get_json()["code"] == "FORBIDDEN"

    def test_update_rules_dm_success(self, client, session, cleanup_database):
        """Test that DM can update game rules."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        template = create_ruleset_template(session)
        game = create_game_with_dm(session, dm, ruleset_template=template)
        session.commit()
        
        token = get_auth_token(client, "dm@example.com")
        new_rules = {"character": {"level": {"default": 3}}}
        response = client.put(
            f"/api/v1/game/{game.id}/rules",
            json={"custom_rules": new_rules},
            headers=auth_headers(token),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["custom_rules"] == new_rules
        assert data["effective_rules"]["character"]["level"]["default"] == 3

    def test_update_rules_admin_success(self, client, session, cleanup_database):
        """Test that admin can update any game's rules."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        admin = create_test_user(
            session, "admin@example.com", "Admin", "admin", role=UserRole.ADMIN.value
        )
        
        template = create_ruleset_template(session)
        game = create_game_with_dm(session, dm, ruleset_template=template)
        session.commit()
        
        token = get_auth_token(client, "admin@example.com")
        new_rules = {"combat": {"turn_timeout": {"enabled": False}}}
        response = client.put(
            f"/api/v1/game/{game.id}/rules",
            json={"custom_rules": new_rules},
            headers=auth_headers(token),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["effective_rules"]["combat"]["turn_timeout"]["enabled"] is False

    def test_update_rules_clear_custom_rules(self, client, session, cleanup_database):
        """Test clearing custom rules by setting to None."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        template = create_ruleset_template(session)
        custom_rules = {"character": {"level": {"default": 5}}}
        game = create_game_with_dm(
            session, dm, ruleset_template=template, custom_rules=custom_rules
        )
        session.commit()
        
        token = get_auth_token(client, "dm@example.com")
        response = client.put(
            f"/api/v1/game/{game.id}/rules",
            json={"custom_rules": None},
            headers=auth_headers(token),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["custom_rules"] is None
        # Effective rules should now be just template rules
        assert data["effective_rules"]["character"]["level"]["default"] == 1

    def test_update_rules_invalid_section(self, client, session, cleanup_database):
        """Test that unknown rule sections are rejected."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()
        
        token = get_auth_token(client, "dm@example.com")
        invalid_rules = {"unknown_section": {"some_key": "value"}}
        response = client.put(
            f"/api/v1/game/{game.id}/rules",
            json={"custom_rules": invalid_rules},
            headers=auth_headers(token),
        )
        
        assert response.status_code == 400
        assert response.get_json()["code"] == "VALIDATION_ERROR"
        assert "unknown" in response.get_json()["message"].lower()

    def test_update_rules_no_body(self, client, session, cleanup_database):
        """Test that request without body returns error."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()
        
        token = get_auth_token(client, "dm@example.com")
        response = client.put(
            f"/api/v1/game/{game.id}/rules",
            headers=auth_headers(token),
        )
        
        assert response.status_code == 400
        assert response.get_json()["code"] == "VALIDATION_ERROR"

    def test_update_rules_persists_changes(self, client, session, cleanup_database):
        """Test that rule changes are persisted to database."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        template = create_ruleset_template(session)
        game = create_game_with_dm(session, dm, ruleset_template=template)
        session.commit()
        game_id = game.id
        
        token = get_auth_token(client, "dm@example.com")
        new_rules = {"character": {"level": {"default": 10}}}
        client.put(
            f"/api/v1/game/{game_id}/rules",
            json={"custom_rules": new_rules},
            headers=auth_headers(token),
        )
        
        # Verify by fetching again
        response = client.get(
            f"/api/v1/game/{game_id}/rules", headers=auth_headers(token)
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["custom_rules"] == new_rules
        assert data["effective_rules"]["character"]["level"]["default"] == 10

