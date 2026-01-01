"""
Tests for Encounter CRUD API endpoints.
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
from app.domain.encounters.models import (
    Encounter,
    EncounterStatus,
    EncounterDifficulty,
)
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


def create_encounter(
    session,
    game: Game,
    name: str = "Test Encounter",
    status: EncounterStatus = EncounterStatus.DRAFT,
    difficulty: EncounterDifficulty = None,
):
    """Helper to create an encounter."""
    encounter = Encounter(
        game_id=game.id,
        name=name,
        status=status,
        difficulty=difficulty,
        description="A test encounter",
        location="Test Location",
        estimated_xp=100,
        notes="DM notes",
    )
    session.add(encounter)
    session.flush()
    return encounter


class TestCreateEncounter:
    """Tests for POST /api/v1/game/<id>/encounter endpoint."""

    def test_create_encounter_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.post("/api/v1/game/1/encounter", json={"name": "Test"})

        assert response.status_code == 401

    def test_create_encounter_game_not_found(self, client, session, cleanup_database):
        """Test creating encounter for non-existent game returns 404."""
        user = create_test_user(session, "test@example.com", "Test User")
        session.commit()

        token = get_auth_token(client, "test@example.com")
        response = client.post(
            "/api/v1/game/9999/encounter",
            json={"name": "Test Encounter"},
            headers=auth_headers(token),
        )

        assert response.status_code == 404
        assert response.get_json()["code"] == "GAME_NOT_FOUND"

    def test_create_encounter_player_forbidden(self, client, session, cleanup_database):
        """Test that players cannot create encounters."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/encounter",
            json={"name": "Test Encounter"},
            headers=auth_headers(token),
        )

        assert response.status_code == 403
        assert response.get_json()["code"] == "FORBIDDEN"

    def test_create_encounter_dm_success(self, client, session, cleanup_database):
        """Test that DM can create encounters."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/encounter",
            json={
                "name": "Goblin Ambush",
                "description": "A group of goblins attacks the party",
                "location": "Forest Road",
                "difficulty": "MEDIUM",
                "estimated_xp": 150,
                "notes": "Surprise round for goblins",
            },
            headers=auth_headers(token),
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "Goblin Ambush"
        assert data["status"] == "DRAFT"
        assert data["description"] == "A group of goblins attacks the party"
        assert data["location"] == "Forest Road"
        assert data["difficulty"] == "MEDIUM"
        assert data["estimated_xp"] == 150
        assert data["notes"] == "Surprise round for goblins"
        assert data["game_id"] == game.id
        assert data["participants"] == []

    def test_create_encounter_minimal(self, client, session, cleanup_database):
        """Test creating encounter with only required fields."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/encounter",
            json={"name": "Simple Encounter"},
            headers=auth_headers(token),
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "Simple Encounter"
        assert data["status"] == "DRAFT"
        assert data["difficulty"] is None
        assert data["estimated_xp"] is None

    def test_create_encounter_invalid_difficulty(self, client, session, cleanup_database):
        """Test that invalid difficulty returns error."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/encounter",
            json={"name": "Test", "difficulty": "IMPOSSIBLE"},
            headers=auth_headers(token),
        )

        assert response.status_code == 400
        assert response.get_json()["code"] == "VALIDATION_ERROR"

    def test_create_encounter_empty_name(self, client, session, cleanup_database):
        """Test that empty name returns error."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/encounter",
            json={"name": "   "},
            headers=auth_headers(token),
        )

        assert response.status_code == 400
        assert response.get_json()["code"] == "VALIDATION_ERROR"

    def test_create_encounter_invalid_xp(self, client, session, cleanup_database):
        """Test that non-integer XP returns error."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.post(
            f"/api/v1/game/{game.id}/encounter",
            json={"name": "Test", "estimated_xp": "not a number"},
            headers=auth_headers(token),
        )

        assert response.status_code == 400
        assert response.get_json()["code"] == "VALIDATION_ERROR"


class TestGetGameEncounters:
    """Tests for GET /api/v1/game/<id>/encounters endpoint."""

    def test_get_encounters_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.get("/api/v1/game/1/encounters")

        assert response.status_code == 401

    def test_get_encounters_not_member(self, client, session, cleanup_database):
        """Test that non-members get forbidden error."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        other = create_test_user(session, "other@example.com", "Other", "other")

        game = create_game_with_dm(session, dm)
        create_encounter(session, game, "Encounter 1")
        session.commit()

        token = get_auth_token(client, "other@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounters", headers=auth_headers(token)
        )

        assert response.status_code == 403

    def test_get_encounters_as_dm(self, client, session, cleanup_database):
        """Test that DM gets all encounters."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        create_encounter(session, game, "Encounter 1")
        create_encounter(session, game, "Encounter 2", status=EncounterStatus.READY)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounters", headers=auth_headers(token)
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        assert "participants" in data[0]

    def test_get_encounters_as_player(self, client, session, cleanup_database):
        """Test that players can view encounters."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        create_encounter(session, game, "Encounter 1")
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounters", headers=auth_headers(token)
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1

    def test_get_encounters_filter_by_status(self, client, session, cleanup_database):
        """Test filtering by encounter status."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        create_encounter(session, game, "Draft Encounter", status=EncounterStatus.DRAFT)
        create_encounter(session, game, "Ready Encounter", status=EncounterStatus.READY)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounters?status=DRAFT",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "Draft Encounter"

    def test_get_encounters_invalid_status(self, client, session, cleanup_database):
        """Test that invalid status filter returns error."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounters?status=INVALID",
            headers=auth_headers(token),
        )

        assert response.status_code == 400
        assert response.get_json()["code"] == "VALIDATION_ERROR"


class TestGetEncounter:
    """Tests for GET /api/v1/game/<id>/encounter/<id> endpoint."""

    def test_get_encounter_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.get("/api/v1/game/1/encounter/1")

        assert response.status_code == 401

    def test_get_encounter_not_found(self, client, session, cleanup_database):
        """Test getting non-existent encounter returns 404."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/9999", headers=auth_headers(token)
        )

        assert response.status_code == 404
        assert response.get_json()["code"] == "ENCOUNTER_NOT_FOUND"

    def test_get_encounter_wrong_game(self, client, session, cleanup_database):
        """Test getting encounter from wrong game returns 404."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game1 = create_game_with_dm(session, dm, "Game 1")
        game2 = create_game_with_dm(session, dm, "Game 2")
        encounter = create_encounter(session, game1, "Encounter")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game2.id}/encounter/{encounter.id}",
            headers=auth_headers(token),
        )

        assert response.status_code == 404

    def test_get_encounter_as_dm(self, client, session, cleanup_database):
        """Test DM gets full encounter data."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        encounter = create_encounter(
            session, game, "Goblin Ambush", difficulty=EncounterDifficulty.HARD
        )
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Goblin Ambush"
        assert data["difficulty"] == "HARD"
        assert data["notes"] == "DM notes"
        assert "participants" in data

    def test_get_encounter_as_player(self, client, session, cleanup_database):
        """Test player can view encounters."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        encounter = create_encounter(session, game, "Encounter")
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Encounter"

    def test_get_encounter_not_member(self, client, session, cleanup_database):
        """Test non-member cannot view encounter."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        other = create_test_user(session, "other@example.com", "Other", "other")

        game = create_game_with_dm(session, dm)
        encounter = create_encounter(session, game, "Encounter")
        session.commit()

        token = get_auth_token(client, "other@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}",
            headers=auth_headers(token),
        )

        assert response.status_code == 403


class TestUpdateEncounter:
    """Tests for PUT /api/v1/game/<id>/encounter/<id> endpoint."""

    def test_update_encounter_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.put("/api/v1/game/1/encounter/1", json={"name": "New"})

        assert response.status_code == 401

    def test_update_encounter_player_forbidden(self, client, session, cleanup_database):
        """Test that players cannot update encounters."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        encounter = create_encounter(session, game, "Encounter")
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.put(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}",
            json={"name": "New Name"},
            headers=auth_headers(token),
        )

        assert response.status_code == 403

    def test_update_encounter_dm_success(self, client, session, cleanup_database):
        """Test that DM can update encounters."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        encounter = create_encounter(session, game, "Old Name")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.put(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}",
            json={
                "name": "New Name",
                "difficulty": "DEADLY",
                "description": "Updated description",
                "estimated_xp": 500,
            },
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "New Name"
        assert data["difficulty"] == "DEADLY"
        assert data["description"] == "Updated description"
        assert data["estimated_xp"] == 500

    def test_update_encounter_partial(self, client, session, cleanup_database):
        """Test partial update only changes specified fields."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        encounter = create_encounter(
            session, game, "Original", difficulty=EncounterDifficulty.MEDIUM
        )
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.put(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}",
            json={"notes": "Updated notes only"},
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Original"  # Unchanged
        assert data["difficulty"] == "MEDIUM"  # Unchanged
        assert data["notes"] == "Updated notes only"  # Changed

    def test_update_encounter_empty_name(self, client, session, cleanup_database):
        """Test that empty name is rejected."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        encounter = create_encounter(session, game, "Encounter")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.put(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}",
            json={"name": "   "},
            headers=auth_headers(token),
        )

        assert response.status_code == 400

    def test_update_encounter_not_found(self, client, session, cleanup_database):
        """Test updating non-existent encounter returns 404."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.put(
            f"/api/v1/game/{game.id}/encounter/9999",
            json={"name": "Test"},
            headers=auth_headers(token),
        )

        assert response.status_code == 404

    def test_update_active_encounter_forbidden(self, client, session, cleanup_database):
        """Test that active encounters cannot be updated."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        encounter = create_encounter(
            session, game, "Active Encounter", status=EncounterStatus.ACTIVE
        )
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.put(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}",
            json={"name": "New Name"},
            headers=auth_headers(token),
        )

        assert response.status_code == 409
        assert response.get_json()["code"] == "CONFLICT"


class TestDeleteEncounter:
    """Tests for DELETE /api/v1/game/<id>/encounter/<id> endpoint."""

    def test_delete_encounter_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.delete("/api/v1/game/1/encounter/1")

        assert response.status_code == 401

    def test_delete_encounter_player_forbidden(self, client, session, cleanup_database):
        """Test that players cannot delete encounters."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        encounter = create_encounter(session, game, "Encounter")
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.delete(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}",
            headers=auth_headers(token),
        )

        assert response.status_code == 403

    def test_delete_encounter_dm_success(self, client, session, cleanup_database):
        """Test that DM can delete encounters."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        encounter = create_encounter(session, game, "Encounter")
        encounter_id = encounter.id
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.delete(
            f"/api/v1/game/{game.id}/encounter/{encounter_id}",
            headers=auth_headers(token),
        )

        assert response.status_code == 204

        # Verify encounter is deleted
        get_response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter_id}",
            headers=auth_headers(token),
        )
        assert get_response.status_code == 404

    def test_delete_encounter_not_found(self, client, session, cleanup_database):
        """Test deleting non-existent encounter returns 404."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.delete(
            f"/api/v1/game/{game.id}/encounter/9999",
            headers=auth_headers(token),
        )

        assert response.status_code == 404

    def test_delete_active_encounter_forbidden(self, client, session, cleanup_database):
        """Test that active encounters cannot be deleted."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        encounter = create_encounter(
            session, game, "Active Encounter", status=EncounterStatus.ACTIVE
        )
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.delete(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}",
            headers=auth_headers(token),
        )

        assert response.status_code == 409
        assert response.get_json()["code"] == "CONFLICT"

    def test_delete_ready_encounter_success(self, client, session, cleanup_database):
        """Test that READY encounters can be deleted."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        encounter = create_encounter(
            session, game, "Ready Encounter", status=EncounterStatus.READY
        )
        encounter_id = encounter.id
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.delete(
            f"/api/v1/game/{game.id}/encounter/{encounter_id}",
            headers=auth_headers(token),
        )

        assert response.status_code == 204

