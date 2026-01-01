"""
Tests for Encounter Logs and State API endpoints.
"""

import pytest
from datetime import datetime
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
    EncounterState,
    EncounterStateStatus,
    CombatLog,
    CombatActionType,
    ActorType,
    EncounterParticipant,
    ParticipantType,
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
):
    """Helper to create an encounter."""
    encounter = Encounter(
        game_id=game.id,
        name=name,
        status=status,
        description="A test encounter",
    )
    session.add(encounter)
    session.flush()
    return encounter


def create_encounter_state(
    session,
    encounter: Encounter,
    status: EncounterStateStatus = EncounterStateStatus.IN_PROGRESS,
):
    """Helper to create encounter state."""
    state = EncounterState(
        encounter_id=encounter.id,
        current_round=1,
        current_turn_index=0,
        initiative_order=[],
        combatants_state={},
        status=status,
    )
    session.add(state)
    session.flush()
    return state


def create_combat_log(
    session,
    encounter: Encounter,
    user: User,
    round_number: int = 1,
    action_type: CombatActionType = CombatActionType.ATTACK,
    actor_name: str = "Fighter",
):
    """Helper to create a combat log entry."""
    log = CombatLog(
        encounter_id=encounter.id,
        round_number=round_number,
        action_type=action_type,
        actor_type=ActorType.CHARACTER,
        actor_id=1,
        actor_name=actor_name,
        target_type=ActorType.NPC,
        target_id=1,
        target_name="Goblin",
        data={"roll": 15, "damage": 8},
        result={"hit": True},
        created_by_user_id=user.id,
    )
    session.add(log)
    session.flush()
    return log


def create_character(session, game: Game, user: User, name: str = "Test Character"):
    """Helper to create a character."""
    character = Character(
        game_id=game.id,
        user_id=user.id,
        name=name,
        status=CharacterStatus.APPROVED,
        data={"hp": 30, "max_hp": 30, "class": "Fighter"},
    )
    session.add(character)
    session.flush()
    return character


class TestGetEncounterLogs:
    """Tests for GET /api/v1/game/<id>/encounter/<id>/logs endpoint."""

    def test_get_logs_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.get("/api/v1/game/1/encounter/1/logs")

        assert response.status_code == 401

    def test_get_logs_encounter_not_found(self, client, session, cleanup_database):
        """Test getting logs for non-existent encounter returns 404."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/9999/logs",
            headers=auth_headers(token),
        )

        assert response.status_code == 404
        assert response.get_json()["code"] == "ENCOUNTER_NOT_FOUND"

    def test_get_logs_not_member(self, client, session, cleanup_database):
        """Test that non-members cannot get logs."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        other = create_test_user(session, "other@example.com", "Other", "other")

        game = create_game_with_dm(session, dm)
        encounter = create_encounter(session, game, status=EncounterStatus.ACTIVE)
        create_combat_log(session, encounter, dm)
        session.commit()

        token = get_auth_token(client, "other@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}/logs",
            headers=auth_headers(token),
        )

        assert response.status_code == 403

    def test_get_logs_success(self, client, session, cleanup_database):
        """Test successfully getting combat logs."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        encounter = create_encounter(session, game, status=EncounterStatus.ACTIVE)
        
        create_combat_log(session, encounter, dm, round_number=1, actor_name="Fighter")
        create_combat_log(session, encounter, dm, round_number=1, actor_name="Wizard")
        create_combat_log(session, encounter, dm, round_number=2, actor_name="Fighter")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}/logs",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 3
        assert data[0]["actor_name"] == "Fighter"
        assert data[0]["round_number"] == 1
        assert "data" in data[0]
        assert "result" in data[0]

    def test_get_logs_filter_by_round(self, client, session, cleanup_database):
        """Test filtering logs by round number."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        encounter = create_encounter(session, game, status=EncounterStatus.ACTIVE)
        
        create_combat_log(session, encounter, dm, round_number=1, actor_name="Round1")
        create_combat_log(session, encounter, dm, round_number=2, actor_name="Round2")
        create_combat_log(session, encounter, dm, round_number=2, actor_name="Round2-2")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}/logs?round=2",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        assert all(log["round_number"] == 2 for log in data)

    def test_get_logs_with_limit(self, client, session, cleanup_database):
        """Test limiting number of logs returned."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        encounter = create_encounter(session, game, status=EncounterStatus.ACTIVE)
        
        # Create 5 logs
        for i in range(5):
            create_combat_log(session, encounter, dm, round_number=i+1, actor_name=f"Actor{i}")
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}/logs?limit=3",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 3

    def test_get_logs_wrong_game(self, client, session, cleanup_database):
        """Test getting logs for encounter in wrong game returns 404."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game1 = create_game_with_dm(session, dm, "Game 1")
        game2 = create_game_with_dm(session, dm, "Game 2")
        encounter = create_encounter(session, game1, status=EncounterStatus.ACTIVE)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game2.id}/encounter/{encounter.id}/logs",
            headers=auth_headers(token),
        )

        assert response.status_code == 404

    def test_get_logs_player_can_view(self, client, session, cleanup_database):
        """Test that players can view combat logs."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        encounter = create_encounter(session, game, status=EncounterStatus.ACTIVE)
        create_combat_log(session, encounter, dm)
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}/logs",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        assert len(response.get_json()) == 1


class TestGetEncounterState:
    """Tests for GET /api/v1/game/<id>/encounter/<id>/state endpoint."""

    def test_get_state_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.get("/api/v1/game/1/encounter/1/state")

        assert response.status_code == 401

    def test_get_state_encounter_not_found(self, client, session, cleanup_database):
        """Test getting state for non-existent encounter returns 404."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/9999/state",
            headers=auth_headers(token),
        )

        assert response.status_code == 404

    def test_get_state_not_member(self, client, session, cleanup_database):
        """Test that non-members cannot get state."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        other = create_test_user(session, "other@example.com", "Other", "other")

        game = create_game_with_dm(session, dm)
        encounter = create_encounter(session, game, status=EncounterStatus.ACTIVE)
        session.commit()

        token = get_auth_token(client, "other@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}/state",
            headers=auth_headers(token),
        )

        assert response.status_code == 403

    def test_get_state_no_active_combat(self, client, session, cleanup_database):
        """Test getting state for encounter without active combat."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        encounter = create_encounter(session, game, status=EncounterStatus.DRAFT)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}/state",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["state"] is None
        assert data["encounter"]["id"] == encounter.id
        assert data["recent_logs"] == []

    def test_get_state_active_combat(self, client, session, cleanup_database):
        """Test getting full state for active combat."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game = create_game_with_dm(session, dm)
        encounter = create_encounter(session, game, status=EncounterStatus.ACTIVE)
        
        state = create_encounter_state(session, encounter)
        create_combat_log(session, encounter, dm)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}/state",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        
        assert data["encounter"]["id"] == encounter.id
        assert data["encounter"]["status"] == "ACTIVE"
        
        assert data["state"] is not None
        assert data["state"]["current_round"] == 1
        assert data["state"]["status"] == "IN_PROGRESS"
        
        assert len(data["recent_logs"]) == 1

    def test_get_state_with_participants(self, client, session, cleanup_database):
        """Test state includes encounter participants."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        player = create_test_user(session, "player@example.com", "Player", "player")
        
        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        
        character = create_character(session, game, player, "Fighter")
        encounter = create_encounter(session, game, status=EncounterStatus.ACTIVE)
        
        # Add participant
        participant = EncounterParticipant(
            encounter_id=encounter.id,
            participant_type=ParticipantType.CHARACTER,
            participant_id=character.id,
            quantity=1,
            instance_index=1,
        )
        session.add(participant)
        
        state = EncounterState(
            encounter_id=encounter.id,
            current_round=2,
            current_turn_index=0,
            initiative_order=[{"key": f"CHARACTER_{character.id}", "initiative": 18}],
            combatants_state={
                f"CHARACTER_{character.id}": {
                    "name": "Fighter",
                    "current_hp": 25,
                    "max_hp": 30,
                    "conditions": [],
                    "connection_status": "CONNECTED",
                }
            },
            status=EncounterStateStatus.IN_PROGRESS,
        )
        session.add(state)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}/state",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        
        assert len(data["encounter"]["participants"]) == 1
        assert data["encounter"]["participants"][0]["participant_type"] == "CHARACTER"
        
        assert data["state"]["current_round"] == 2
        assert len(data["state"]["initiative_order"]) == 1
        assert f"CHARACTER_{character.id}" in data["state"]["combatants_state"]

    def test_get_state_wrong_game(self, client, session, cleanup_database):
        """Test getting state for encounter in wrong game returns 404."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        game1 = create_game_with_dm(session, dm, "Game 1")
        game2 = create_game_with_dm(session, dm, "Game 2")
        encounter = create_encounter(session, game1, status=EncounterStatus.ACTIVE)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game2.id}/encounter/{encounter.id}/state",
            headers=auth_headers(token),
        )

        assert response.status_code == 404

    def test_get_state_player_can_view(self, client, session, cleanup_database):
        """Test that players can view encounter state."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)
        encounter = create_encounter(session, game, status=EncounterStatus.ACTIVE)
        create_encounter_state(session, encounter)
        session.commit()

        token = get_auth_token(client, "player@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}/state",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["state"] is not None

