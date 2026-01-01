"""
Tests for NPC CRUD API endpoints.

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
    npc_type: NPCType = NPCType.NEUTRAL,
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
        data={"class": "Commoner", "level": 1},
    )
    session.add(npc)
    session.flush()
    return npc


class TestCreateNPC:
    """Tests for POST /api/v1/game/<id>/npc endpoint."""

    def test_create_npc_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.post("/api/v1/game/1/npc", json={"name": "Test"})

        assert response.status_code == 401

    def test_create_npc_game_not_found(self, client, session, cleanup_database):
        """Test creating NPC for non-existent game returns 404."""
        user = create_test_user(session, "test@example.com", "Test User")
        session.commit()

        token = get_auth_token(client, "test@example.com")
        response = client.post(
            "/api/v1/game/9999/npc",
            json={"name": "Test NPC"},
            headers=auth_headers(token),
        )

        assert response.status_code == 404
        assert response.get_json()["code"] == "GAME_NOT_FOUND"

    def test_create_npc_player_forbidden(self, client, session, cleanup_database):
        """Test that players cannot create NPCs."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/npc",
            json={"name": "Test NPC"},
            headers=auth_headers(token),
        )

        assert response.status_code == 403
        assert response.get_json()["code"] == "FORBIDDEN"

    def test_create_npc_dm_success(self, client, session, cleanup_database):
        """Test that DM can create NPCs."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/npc",
            json={
                "name": "Goblin Warrior",
                "npc_type": "ENEMY",
                "description": "A fierce goblin",
                "stats": {"hp": 15, "ac": 14},
                "data": {"level": 2},
            },
            headers=auth_headers(token),
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "Goblin Warrior"
        assert data["npc_type"] == "ENEMY"
        assert data["status"] == "ACTIVE"
        assert data["description"] == "A fierce goblin"
        assert data["stats"]["hp"] == 15
        assert data["game_id"] == game.id

    def test_create_npc_default_type(self, client, session, cleanup_database):
        """Test that default NPC type is NEUTRAL."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/npc",
            json={"name": "Villager"},
            headers=auth_headers(token),
        )

        assert response.status_code == 201
        assert response.get_json()["npc_type"] == "NEUTRAL"

    def test_create_npc_invalid_type(self, client, session, cleanup_database):
        """Test that invalid NPC type returns error."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/npc",
            json={"name": "Test", "npc_type": "INVALID"},
            headers=auth_headers(token),
        )

        assert response.status_code == 400
        assert response.get_json()["code"] == "VALIDATION_ERROR"

    def test_create_npc_empty_name(self, client, session, cleanup_database):
        """Test that empty name returns error."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/npc",
            json={"name": "   "},
            headers=auth_headers(token),
        )

        assert response.status_code == 400
        assert response.get_json()["code"] == "VALIDATION_ERROR"


class TestGetGameNPCs:
    """Tests for GET /api/v1/game/<id>/npcs endpoint."""

    def test_get_npcs_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.get("/api/v1/game/1/npcs")

        assert response.status_code == 401

    def test_get_npcs_not_member(self, client, session, cleanup_database):
        """Test that non-members get empty list."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        other = create_test_user(session, "other@example.com", "Other", "other")

        game = create_game_with_dm(session, dm)
        create_npc(session, game, "Goblin")
        session.commit()

        token = get_auth_token(client, "other@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/npcs", headers=auth_headers(token)
        )

        assert response.status_code == 200
        assert response.get_json() == []

    def test_get_npcs_as_dm(self, client, session, cleanup_database):
        """Test that DM gets full NPC data."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        create_npc(session, game, "Goblin", NPCType.ENEMY)
        create_npc(session, game, "Merchant", NPCType.NEUTRAL)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/npcs", headers=auth_headers(token)
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        # DM should see full data including stats
        assert "stats" in data[0]
        assert "data" in data[0]

    def test_get_npcs_as_player(self, client, session, cleanup_database):
        """Test that players get limited NPC view."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        create_npc(session, game, "Goblin", NPCType.ENEMY)
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/npcs", headers=auth_headers(token)
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        # Players should NOT see stats and data
        assert "stats" not in data[0]
        assert "data" not in data[0]

    def test_get_npcs_filter_active_only(self, client, session, cleanup_database):
        """Test filtering by active status."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        create_npc(session, game, "Active NPC", status=NPCStatus.ACTIVE)
        create_npc(session, game, "Defeated NPC", status=NPCStatus.DEFEATED)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/npcs?active_only=true",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "Active NPC"

    def test_get_npcs_filter_by_type(self, client, session, cleanup_database):
        """Test filtering by NPC type."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        create_npc(session, game, "Goblin", npc_type=NPCType.ENEMY)
        create_npc(session, game, "Merchant", npc_type=NPCType.NEUTRAL)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/npcs?npc_type=ENEMY",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "Goblin"


class TestGetNPC:
    """Tests for GET /api/v1/game/<id>/npc/<id> endpoint."""

    def test_get_npc_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.get("/api/v1/game/1/npc/1")

        assert response.status_code == 401

    def test_get_npc_not_found(self, client, session, cleanup_database):
        """Test getting non-existent NPC returns 404."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/npc/9999", headers=auth_headers(token)
        )

        assert response.status_code == 404
        assert response.get_json()["code"] == "NPC_NOT_FOUND"

    def test_get_npc_wrong_game(self, client, session, cleanup_database):
        """Test getting NPC from wrong game returns 404."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game1 = create_game_with_dm(session, dm, "Game 1")
        game2 = create_game_with_dm(session, dm, "Game 2")
        npc = create_npc(session, game1, "Goblin")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game2.id}/npc/{npc.id}", headers=auth_headers(token)
        )

        assert response.status_code == 404

    def test_get_npc_as_dm(self, client, session, cleanup_database):
        """Test DM gets full NPC data."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        npc = create_npc(session, game, "Goblin")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/npc/{npc.id}", headers=auth_headers(token)
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Goblin"
        assert "stats" in data
        assert "data" in data

    def test_get_npc_as_player(self, client, session, cleanup_database):
        """Test player gets limited NPC view."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        npc = create_npc(session, game, "Goblin")
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/npc/{npc.id}", headers=auth_headers(token)
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Goblin"
        assert "stats" not in data
        assert "data" not in data


class TestUpdateNPC:
    """Tests for PUT /api/v1/game/<id>/npc/<id> endpoint."""

    def test_update_npc_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.put("/api/v1/game/1/npc/1", json={"name": "New"})

        assert response.status_code == 401

    def test_update_npc_player_forbidden(self, client, session, cleanup_database):
        """Test that players cannot update NPCs."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        npc = create_npc(session, game, "Goblin")
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.put(
            f"/api/v1/game/{game.id}/npc/{npc.id}",
            json={"name": "New Name"},
            headers=auth_headers(token),
        )

        assert response.status_code == 403

    def test_update_npc_dm_success(self, client, session, cleanup_database):
        """Test that DM can update NPCs."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        npc = create_npc(session, game, "Goblin")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.put(
            f"/api/v1/game/{game.id}/npc/{npc.id}",
            json={
                "name": "Hobgoblin",
                "npc_type": "BOSS",
                "description": "Upgraded goblin",
                "stats": {"hp": 50, "ac": 18},
            },
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Hobgoblin"
        assert data["npc_type"] == "BOSS"
        assert data["description"] == "Upgraded goblin"
        assert data["stats"]["hp"] == 50

    def test_update_npc_status(self, client, session, cleanup_database):
        """Test updating NPC status."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        npc = create_npc(session, game, "Goblin")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.put(
            f"/api/v1/game/{game.id}/npc/{npc.id}",
            json={"status": "DEFEATED"},
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        assert response.get_json()["status"] == "DEFEATED"

    def test_update_npc_empty_name(self, client, session, cleanup_database):
        """Test that empty name is rejected."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        npc = create_npc(session, game, "Goblin")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.put(
            f"/api/v1/game/{game.id}/npc/{npc.id}",
            json={"name": "   "},
            headers=auth_headers(token),
        )

        assert response.status_code == 400

    def test_update_npc_not_found(self, client, session, cleanup_database):
        """Test updating non-existent NPC returns 404."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.put(
            f"/api/v1/game/{game.id}/npc/9999",
            json={"name": "Test"},
            headers=auth_headers(token),
        )

        assert response.status_code == 404


class TestDeleteNPC:
    """Tests for DELETE /api/v1/game/<id>/npc/<id> endpoint."""

    def test_delete_npc_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.delete("/api/v1/game/1/npc/1")

        assert response.status_code == 401

    def test_delete_npc_player_forbidden(self, client, session, cleanup_database):
        """Test that players cannot delete NPCs."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        npc = create_npc(session, game, "Goblin")
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.delete(
            f"/api/v1/game/{game.id}/npc/{npc.id}",
            headers=auth_headers(token),
        )

        assert response.status_code == 403

    def test_delete_npc_dm_success(self, client, session, cleanup_database):
        """Test that DM can delete NPCs."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        npc = create_npc(session, game, "Goblin")
        npc_id = npc.id
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.delete(
            f"/api/v1/game/{game.id}/npc/{npc_id}",
            headers=auth_headers(token),
        )

        assert response.status_code == 204

        # Verify NPC is deleted
        get_response = client.get(
            f"/api/v1/game/{game.id}/npc/{npc_id}",
            headers=auth_headers(token),
        )
        assert get_response.status_code == 404

    def test_delete_npc_not_found(self, client, session, cleanup_database):
        """Test deleting non-existent NPC returns 404."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.delete(
            f"/api/v1/game/{game.id}/npc/9999",
            headers=auth_headers(token),
        )

        assert response.status_code == 404

