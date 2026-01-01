"""
Tests for NPC Conversion API endpoints.

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
from app.domain.npcs.models import NPC, NPCType, NPCStatus
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


def create_game_with_dm(session, dm_user: User, name: str = "Test Game"):
    """Helper to create a game with a DM membership."""
    game = Game(
        name=name,
        dm_user_id=dm_user.id,
        status=GameStatus.ACTIVE,
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


def create_npc(
    session,
    game: Game,
    name: str = "Test NPC",
    npc_type: NPCType = NPCType.COMPANION,
    status: NPCStatus = NPCStatus.ACTIVE,
):
    """Helper to create an NPC."""
    npc = NPC(
        game_id=game.id,
        name=name,
        npc_type=npc_type,
        status=status,
        description="A test NPC",
        stats={"hp": 20, "ac": 12},
        data={"class": "Fighter", "level": 5},
    )
    session.add(npc)
    session.flush()
    return npc


def create_character(
    session,
    game: Game,
    user: User,
    name: str = "Test Character",
    status: CharacterStatus = CharacterStatus.APPROVED,
):
    """Helper to create a character."""
    character = Character(
        game_id=game.id,
        user_id=user.id,
        name=name,
        status=status,
        data={"class": "Wizard", "level": 3, "hp": 15, "ac": 13},
    )
    session.add(character)
    session.flush()
    return character


class TestConvertNPCToCharacter:
    """Tests for POST /api/v1/game/<id>/npc/<id>/convert-to-character endpoint."""

    def test_convert_npc_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.post(
            "/api/v1/game/1/npc/1/convert-to-character",
            json={"user_id": 1},
        )

        assert response.status_code == 401

    def test_convert_npc_player_forbidden(self, client, session, cleanup_database):
        """Test that players cannot convert NPCs."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")
        new_player = create_test_user(session, "new@example.com", "New Player", "new")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        add_player_to_game(session, game, new_player)
        npc = create_npc(session, game, "Companion")
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/npc/{npc.id}/convert-to-character",
            json={"user_id": new_player.id},
            headers=auth_headers(token),
        )

        assert response.status_code == 403

    def test_convert_npc_dm_success(self, client, session, cleanup_database):
        """Test that DM can convert NPC to character."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        new_player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, new_player)
        npc = create_npc(session, game, "Companion NPC")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/npc/{npc.id}/convert-to-character",
            json={"user_id": new_player.id},
            headers=auth_headers(token),
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "Companion NPC"
        assert data["user_id"] == new_player.id
        assert data["game_id"] == game.id
        assert data["status"] == "APPROVED"  # Auto-approved by DM conversion

    def test_convert_npc_user_not_member(self, client, session, cleanup_database):
        """Test converting NPC to non-member user fails."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        non_member = create_test_user(session, "other@example.com", "Other", "other")

        game = create_game_with_dm(session, dm)
        npc = create_npc(session, game, "Companion")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/npc/{npc.id}/convert-to-character",
            json={"user_id": non_member.id},
            headers=auth_headers(token),
        )

        assert response.status_code == 400
        assert "not an active member" in response.get_json()["message"].lower()

    def test_convert_npc_user_already_has_character(self, client, session, cleanup_database):
        """Test converting NPC to user who already has a character fails."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        create_character(session, game, player, "Existing Character")
        npc = create_npc(session, game, "Companion")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/npc/{npc.id}/convert-to-character",
            json={"user_id": player.id},
            headers=auth_headers(token),
        )

        assert response.status_code == 409
        assert "already has a character" in response.get_json()["message"].lower()

    def test_convert_npc_already_converted(self, client, session, cleanup_database):
        """Test converting already converted NPC fails."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        npc = create_npc(session, game, "Companion", status=NPCStatus.CONVERTED_TO_PC)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/npc/{npc.id}/convert-to-character",
            json={"user_id": player.id},
            headers=auth_headers(token),
        )

        assert response.status_code == 409
        assert "already converted" in response.get_json()["message"].lower()

    def test_convert_npc_not_found(self, client, session, cleanup_database):
        """Test converting non-existent NPC returns 404."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/npc/9999/convert-to-character",
            json={"user_id": 1},
            headers=auth_headers(token),
        )

        assert response.status_code == 404

    def test_convert_npc_missing_user_id(self, client, session, cleanup_database):
        """Test that user_id is required."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        npc = create_npc(session, game, "Companion")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/npc/{npc.id}/convert-to-character",
            json={},
            headers=auth_headers(token),
        )

        assert response.status_code == 400


class TestConvertCharacterToNPC:
    """Tests for POST /api/v1/game/<id>/character/<id>/convert-to-npc endpoint."""

    def test_convert_character_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.post("/api/v1/game/1/character/1/convert-to-npc", json={})

        assert response.status_code == 401

    def test_convert_character_player_forbidden(self, client, session, cleanup_database):
        """Test that players cannot convert characters."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        character = create_character(session, game, player, "My Character")
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/character/{character.id}/convert-to-npc",
            json={},
            headers=auth_headers(token),
        )

        assert response.status_code == 403

    def test_convert_character_dm_success(self, client, session, cleanup_database):
        """Test that DM can convert character to NPC."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        character = create_character(session, game, player, "Player Character")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/character/{character.id}/convert-to-npc",
            json={"npc_type": "COMPANION"},
            headers=auth_headers(token),
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "Player Character"
        assert data["npc_type"] == "COMPANION"
        assert data["status"] == "ACTIVE"
        assert data["converted_from_character_id"] == character.id

    def test_convert_character_default_type(self, client, session, cleanup_database):
        """Test default NPC type is COMPANION."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        character = create_character(session, game, player, "Character")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/character/{character.id}/convert-to-npc",
            json={},
            headers=auth_headers(token),
        )

        assert response.status_code == 201
        assert response.get_json()["npc_type"] == "COMPANION"

    def test_convert_character_custom_type(self, client, session, cleanup_database):
        """Test converting with custom NPC type."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        character = create_character(session, game, player, "Evil Character")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/character/{character.id}/convert-to-npc",
            json={"npc_type": "ENEMY"},
            headers=auth_headers(token),
        )

        assert response.status_code == 201
        assert response.get_json()["npc_type"] == "ENEMY"

    def test_convert_character_already_converted(self, client, session, cleanup_database):
        """Test converting already converted character fails."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        character = create_character(
            session, game, player, "Character", CharacterStatus.CONVERTED_TO_NPC
        )
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/character/{character.id}/convert-to-npc",
            json={},
            headers=auth_headers(token),
        )

        assert response.status_code == 409
        assert "already converted" in response.get_json()["message"].lower()

    def test_convert_character_not_found(self, client, session, cleanup_database):
        """Test converting non-existent character returns 404."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/character/9999/convert-to-npc",
            json={},
            headers=auth_headers(token),
        )

        assert response.status_code == 404

    def test_convert_character_wrong_game(self, client, session, cleanup_database):
        """Test converting character from wrong game returns 404."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game1 = create_game_with_dm(session, dm, "Game 1")
        game2 = create_game_with_dm(session, dm, "Game 2")
        add_player_to_game(session, game1, player)
        character = create_character(session, game1, player, "Character")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game2.id}/character/{character.id}/convert-to-npc",
            json={},
            headers=auth_headers(token),
        )

        assert response.status_code == 404

    def test_convert_character_invalid_type(self, client, session, cleanup_database):
        """Test converting with invalid NPC type returns error."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        character = create_character(session, game, player, "Character")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/character/{character.id}/convert-to-npc",
            json={"npc_type": "INVALID"},
            headers=auth_headers(token),
        )

        assert response.status_code == 400

