"""
Tests for Character CRUD API endpoints.

Endpoints tested:
- POST /api/v1/game/<id>/character - Create character
- GET /api/v1/game/<id>/characters - Get game characters
- GET /api/v1/game/<id>/character/<id> - Get specific character
- PUT /api/v1/game/<id>/character/<id> - Update character
- POST /api/v1/game/<id>/character/<id>/approve - Approve character (DM)
- POST /api/v1/game/<id>/character/<id>/reject - Reject character (DM)
- GET /api/v1/game/<id>/my-character - Get current user's character
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
from app.domain.characters.models import Character, CharacterStatus
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
    requires_approval: bool = False,
):
    """Helper to create a game with a DM membership."""
    game = Game(
        name=name,
        dm_user_id=dm_user.id,
        status=GameStatus.ACTIVE,
        settings={"requires_character_approval": requires_approval},
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


def create_character(
    session,
    game: Game,
    user: User,
    name: str = "Test Character",
    status: CharacterStatus = CharacterStatus.APPROVED,
    data: dict = None,
):
    """Helper to create a character."""
    character = Character(
        game_id=game.id,
        user_id=user.id,
        name=name,
        status=status,
        data=data or {"class": "Wizard", "level": 1},
    )
    session.add(character)
    session.flush()
    return character


class TestCreateCharacter:
    """Tests for POST /api/v1/game/<id>/character endpoint."""

    def test_create_character_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.post("/api/v1/game/1/character", json={"name": "Test"})

        assert response.status_code == 401

    def test_create_character_game_not_found(self, client, session, cleanup_database):
        """Test creating character for non-existent game returns 404."""
        user = create_test_user(session, "test@example.com", "Test User")
        session.commit()

        token = get_auth_token(client, "test@example.com")
        response = client.post(
            "/api/v1/game/9999/character",
            json={"name": "Test Character"},
            headers=auth_headers(token),
        )

        assert response.status_code == 404
        assert response.get_json()["code"] == "NOT_FOUND"

    def test_create_character_not_member(self, client, session, cleanup_database):
        """Test creating character when not a game member returns error."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        other = create_test_user(session, "other@example.com", "Other", "other")

        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "other@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/character",
            json={"name": "Test Character"},
            headers=auth_headers(token),
        )

        assert response.status_code == 400
        assert "not an active member" in response.get_json()["message"].lower()

    def test_create_character_success_draft(self, client, session, cleanup_database):
        """Test creating character without submitting for approval."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/character",
            json={
                "name": "Gandalf",
                "data": {"class": "Wizard", "level": 5, "race": "Human"},
                "submit_for_approval": False,
            },
            headers=auth_headers(token),
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "Gandalf"
        assert data["status"] == "DRAFT"
        assert data["data"]["class"] == "Wizard"
        assert data["data"]["level"] == 5
        assert data["game_id"] == game.id
        assert data["user_id"] == player.id

    def test_create_character_submit_for_approval(self, client, session, cleanup_database):
        """Test creating character and submitting for approval."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm, requires_approval=True)
        add_player_to_game(session, game, player)
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/character",
            json={
                "name": "Aragorn",
                "data": {"class": "Ranger", "level": 10},
                "submit_for_approval": True,
            },
            headers=auth_headers(token),
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "Aragorn"
        assert data["status"] == "PENDING_APPROVAL"

    def test_create_character_auto_approve_no_requirement(
        self, client, session, cleanup_database
    ):
        """Test character auto-approved when game doesn't require approval."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm, requires_approval=False)
        add_player_to_game(session, game, player)
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/character",
            json={
                "name": "Legolas",
                "data": {"class": "Ranger", "race": "Elf"},
                "submit_for_approval": True,
            },
            headers=auth_headers(token),
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["status"] == "APPROVED"

    def test_create_character_missing_name(self, client, session, cleanup_database):
        """Test creating character without name returns error."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/character",
            json={"data": {"class": "Wizard"}},
            headers=auth_headers(token),
        )

        assert response.status_code == 400
        assert response.get_json()["code"] == "VALIDATION_ERROR"

    def test_create_character_duplicate(self, client, session, cleanup_database):
        """Test that user cannot create multiple characters in same game."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        create_character(session, game, player, "First Character")
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/character",
            json={"name": "Second Character"},
            headers=auth_headers(token),
        )

        assert response.status_code == 400
        assert "already has a character" in response.get_json()["message"].lower()

    def test_create_character_empty_data(self, client, session, cleanup_database):
        """Test creating character with empty data object."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/character",
            json={"name": "Minimal Character", "data": {}},
            headers=auth_headers(token),
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "Minimal Character"
        assert data["data"] == {}


class TestGetGameCharacters:
    """Tests for GET /api/v1/game/<id>/characters endpoint."""

    def test_get_characters_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.get("/api/v1/game/1/characters")

        assert response.status_code == 401

    def test_get_characters_not_member(self, client, session, cleanup_database):
        """Test that non-members cannot see characters."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        other = create_test_user(session, "other@example.com", "Other", "other")

        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "other@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/characters", headers=auth_headers(token)
        )

        assert response.status_code == 403

    def test_get_characters_as_player(self, client, session, cleanup_database):
        """Test that player sees only approved characters and their own."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player1 = create_test_user(session, "player1@example.com", "Player 1", "p1")
        player2 = create_test_user(session, "player2@example.com", "Player 2", "p2")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player1)
        add_player_to_game(session, game, player2)

        # Player 1: Draft character (should see)
        create_character(session, game, player1, "P1 Draft", CharacterStatus.DRAFT)
        # Player 2: Approved character (should see)
        create_character(session, game, player2, "P2 Approved", CharacterStatus.APPROVED)
        # DM: Pending character (should NOT see)
        create_character(session, game, dm, "DM Pending", CharacterStatus.PENDING_APPROVAL)
        session.commit()

        token = get_auth_token(client, "player1@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/characters", headers=auth_headers(token)
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        names = [c["name"] for c in data]
        assert "P1 Draft" in names
        assert "P2 Approved" in names
        assert "DM Pending" not in names

    def test_get_characters_as_dm(self, client, session, cleanup_database):
        """Test that DM sees all characters except drafts."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)

        create_character(session, game, player, "Draft", CharacterStatus.DRAFT)
        create_character(session, game, player, "Pending", CharacterStatus.PENDING_APPROVAL)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/characters", headers=auth_headers(token)
        )

        assert response.status_code == 200
        data = response.get_json()
        # DM should see pending but not drafts
        assert len(data) == 1
        assert data[0]["name"] == "Pending"

    def test_get_characters_filter_by_status(self, client, session, cleanup_database):
        """Test filtering characters by status."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)

        create_character(session, game, player, "Approved", CharacterStatus.APPROVED)
        create_character(session, game, dm, "Rejected", CharacterStatus.REJECTED)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/characters?status=APPROVED",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "Approved"


class TestGetMyCharacter:
    """Tests for GET /api/v1/game/<id>/my-character endpoint."""

    def test_get_my_character_success(self, client, session, cleanup_database):
        """Test getting current user's character."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        character = create_character(session, game, player, "My Character")
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/my-character", headers=auth_headers(token)
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == character.id
        assert data["name"] == "My Character"

    def test_get_my_character_not_found(self, client, session, cleanup_database):
        """Test getting my character when none exists."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/my-character", headers=auth_headers(token)
        )

        assert response.status_code == 404
        assert response.get_json()["code"] == "CHARACTER_NOT_FOUND"
