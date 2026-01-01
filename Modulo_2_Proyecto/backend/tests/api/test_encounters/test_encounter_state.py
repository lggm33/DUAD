"""
Tests for GET /api/v1/game/<game_id>/encounter/<encounter_id>/state endpoint.

This endpoint is used for client reconnection to sync combat state.
"""

import pytest
from datetime import datetime, timezone

from app.domain.users.models import User, UserRole
from app.domain.games.models import (
    Game,
    GameStatus,
    GameMembership,
    GameRoleInGame,
    GameMembershipStatus,
)
from app.domain.characters.models import Character, CharacterStatus
from app.domain.npcs.models import NPC, NPCType, NPCStatus
from app.domain.encounters.models import (
    Encounter,
    EncounterParticipant,
    EncounterState,
    EncounterStatus,
    EncounterStateStatus,
    ParticipantType,
    CombatLog,
    CombatActionType,
    ActorType,
)
from app.utils.password_hasher import PasswordHasher


def create_test_user(
    session,
    email: str,
    name: str,
    username: str = None,
    role: str = UserRole.USER.value,
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
):
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


def create_character(
    session,
    game: Game,
    user: User,
    name: str = "Test Character",
):
    """Helper to create a character."""
    character = Character(
        game_id=game.id,
        user_id=user.id,
        name=name,
        status=CharacterStatus.APPROVED,
        data={"hp": 20, "max_hp": 20, "class": "Fighter", "level": 1},
    )
    session.add(character)
    session.flush()
    return character


def create_npc(
    session,
    game: Game,
    name: str = "Goblin",
    npc_type: NPCType = NPCType.ENEMY,
):
    """Helper to create an NPC."""
    npc = NPC(
        game_id=game.id,
        name=name,
        npc_type=npc_type,
        status=NPCStatus.ACTIVE,
        stats={"hp": 7, "max_hp": 7, "ac": 15},
        data={"description": "A small green creature"},
    )
    session.add(npc)
    session.flush()
    return npc


def create_encounter(
    session,
    game: Game,
    name: str = "Combat Encounter",
    status: EncounterStatus = EncounterStatus.DRAFT,
):
    """Helper to create an encounter."""
    encounter = Encounter(
        game_id=game.id,
        name=name,
        description="A test encounter",
        location="Dark Cave",
        status=status,
    )
    session.add(encounter)
    session.flush()
    return encounter


def add_character_participant(
    session,
    encounter: Encounter,
    character: Character,
):
    """Helper to add a character participant to an encounter."""
    participant = EncounterParticipant(
        encounter_id=encounter.id,
        participant_type=ParticipantType.CHARACTER,
        participant_id=character.id,
        quantity=1,
        instance_index=1,
    )
    session.add(participant)
    session.flush()
    return participant


def add_npc_participant(
    session,
    encounter: Encounter,
    npc: NPC,
    quantity: int = 1,
    instance_index: int = 1,
):
    """Helper to add an NPC participant to an encounter."""
    participant = EncounterParticipant(
        encounter_id=encounter.id,
        participant_type=ParticipantType.NPC,
        participant_id=npc.id,
        quantity=quantity,
        instance_index=instance_index,
    )
    session.add(participant)
    session.flush()
    return participant


def create_encounter_state(
    session,
    encounter: Encounter,
    status: EncounterStateStatus = EncounterStateStatus.IN_PROGRESS,
):
    """Helper to create an encounter state."""
    state = EncounterState(
        encounter_id=encounter.id,
        current_round=1,
        current_turn_index=0,
        initiative_order=[
            {"key": "CHARACTER_1", "initiative": 18, "name": "Hero"},
            {"key": "NPC_1_1", "initiative": 12, "name": "Goblin"},
        ],
        combatants_state={
            "CHARACTER_1": {
                "name": "Hero",
                "current_hp": 20,
                "max_hp": 20,
                "conditions": [],
                "connection_status": "CONNECTED",
            },
            "NPC_1_1": {
                "name": "Goblin",
                "current_hp": 7,
                "max_hp": 7,
                "conditions": [],
            },
        },
        status=status,
    )
    session.add(state)
    session.flush()
    return state


def create_combat_log(
    session,
    encounter: Encounter,
    action_type: CombatActionType = CombatActionType.ATTACK,
    actor_name: str = "Hero",
    round_number: int = 1,
    user_id: int = None,
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
        result={"hit": True, "damage_dealt": 8},
        created_by_user_id=user_id,
    )
    session.add(log)
    session.flush()
    return log


class TestGetEncounterState:
    """Tests for GET /api/v1/game/<game_id>/encounter/<encounter_id>/state endpoint."""

    def test_get_state_unauthorized(self, client, cleanup_database):
        """Test that unauthenticated request returns 401."""
        response = client.get("/api/v1/game/1/encounter/1/state")

        assert response.status_code == 401

    def test_get_state_encounter_not_found(self, client, session, cleanup_database):
        """Test getting state for non-existent encounter returns 404."""
        user = create_test_user(session, "test@example.com", "Test User")
        session.commit()

        token = get_auth_token(client, "test@example.com")
        response = client.get(
            "/api/v1/game/1/encounter/9999/state",
            headers=auth_headers(token),
        )

        assert response.status_code == 404
        assert response.get_json()["code"] == "NOT_FOUND"

    def test_get_state_not_game_member(self, client, session, cleanup_database):
        """Test that non-member cannot access encounter state."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        other_user = create_test_user(session, "other@example.com", "Other", "other")

        game = create_game_with_dm(session, dm)
        encounter = create_encounter(session, game)
        session.commit()

        token = get_auth_token(client, "other@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}/state",
            headers=auth_headers(token),
        )

        assert response.status_code == 403
        assert response.get_json()["code"] == "FORBIDDEN"

    def test_get_state_wrong_game_id(self, client, session, cleanup_database):
        """Test that accessing encounter with wrong game_id returns 404."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")

        game1 = create_game_with_dm(session, dm, "Game 1")
        game2 = Game(
            name="Game 2",
            dm_user_id=dm.id,
            status=GameStatus.ACTIVE,
        )
        session.add(game2)
        session.flush()

        game2_membership = GameMembership(
            game_id=game2.id,
            user_id=dm.id,
            role_in_game=GameRoleInGame.DM,
            status=GameMembershipStatus.ACTIVE,
        )
        session.add(game2_membership)

        encounter = create_encounter(session, game1)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        # Access encounter from game1 using game2's ID
        response = client.get(
            f"/api/v1/game/{game2.id}/encounter/{encounter.id}/state",
            headers=auth_headers(token),
        )

        assert response.status_code == 404
        assert response.get_json()["code"] == "NOT_FOUND"
        assert "not found in this game" in response.get_json()["message"]

    def test_get_state_draft_encounter_no_state(
        self, client, session, cleanup_database
    ):
        """Test getting state for draft encounter (no EncounterState yet)."""
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
        assert data["encounter"]["id"] == encounter.id
        assert data["encounter"]["name"] == "Combat Encounter"
        assert data["encounter"]["status"] == "DRAFT"
        assert data["state"] is None
        assert data["recent_logs"] == []

    def test_get_state_active_encounter_with_state(
        self, client, session, cleanup_database
    ):
        """Test getting state for active encounter with combat state."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)

        character = create_character(session, game, player, "Hero")
        npc = create_npc(session, game, "Goblin")

        encounter = create_encounter(session, game, status=EncounterStatus.ACTIVE)
        add_character_participant(session, encounter, character)
        add_npc_participant(session, encounter, npc)

        state = create_encounter_state(session, encounter)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}/state",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify encounter data
        assert data["encounter"]["id"] == encounter.id
        assert data["encounter"]["status"] == "ACTIVE"
        assert len(data["encounter"]["participants"]) == 2

        # Verify state data
        assert data["state"] is not None
        assert data["state"]["current_round"] == 1
        assert data["state"]["current_turn_index"] == 0
        assert data["state"]["status"] == "IN_PROGRESS"
        assert len(data["state"]["initiative_order"]) == 2
        assert "CHARACTER_1" in data["state"]["combatants_state"]
        assert "NPC_1_1" in data["state"]["combatants_state"]

    def test_get_state_with_combat_logs(self, client, session, cleanup_database):
        """Test getting state includes recent combat logs."""
        dm = create_test_user(session, "dm@example.com", "DM User")

        game = create_game_with_dm(session, dm)
        encounter = create_encounter(session, game, status=EncounterStatus.ACTIVE)
        state = create_encounter_state(session, encounter)

        # Create multiple combat logs
        for i in range(5):
            create_combat_log(
                session,
                encounter,
                action_type=CombatActionType.ATTACK,
                actor_name=f"Hero {i}",
                round_number=1,
                user_id=dm.id,
            )
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}/state",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()

        assert len(data["recent_logs"]) == 5
        # Verify log structure
        log = data["recent_logs"][0]
        assert "id" in log
        assert "action_type" in log
        assert log["action_type"] == "ATTACK"
        assert "actor_name" in log
        assert "created_at" in log

    def test_get_state_as_player(self, client, session, cleanup_database):
        """Test that players can access encounter state."""
        dm = create_test_user(session, "dm@example.com", "DM User", "dm")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)

        encounter = create_encounter(session, game, status=EncounterStatus.ACTIVE)
        create_encounter_state(session, encounter)
        session.commit()

        # Player requests state
        token = get_auth_token(client, "player@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}/state",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["encounter"]["id"] == encounter.id
        assert data["state"] is not None

    def test_get_state_paused_encounter(self, client, session, cleanup_database):
        """Test getting state for paused encounter."""
        dm = create_test_user(session, "dm@example.com", "DM User")

        game = create_game_with_dm(session, dm)
        encounter = create_encounter(session, game, status=EncounterStatus.PAUSED)
        state = create_encounter_state(
            session, encounter, status=EncounterStateStatus.PAUSED
        )
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}/state",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["encounter"]["status"] == "PAUSED"
        assert data["state"]["status"] == "PAUSED"

    def test_get_state_completed_encounter(self, client, session, cleanup_database):
        """Test getting state for completed encounter (historical view)."""
        dm = create_test_user(session, "dm@example.com", "DM User")

        game = create_game_with_dm(session, dm)
        encounter = create_encounter(session, game, status=EncounterStatus.COMPLETED)
        state = create_encounter_state(
            session, encounter, status=EncounterStateStatus.ENDED
        )

        # Add some logs
        create_combat_log(session, encounter, user_id=dm.id)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}/state",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["encounter"]["status"] == "COMPLETED"
        assert data["state"]["status"] == "ENDED"
        assert len(data["recent_logs"]) == 1

    def test_get_state_participants_structure(self, client, session, cleanup_database):
        """Test that participants are correctly structured in response."""
        dm = create_test_user(session, "dm@example.com", "DM User")
        player = create_test_user(session, "player@example.com", "Player", "player")

        game = create_game_with_dm(session, dm)
        add_player_to_game(session, game, player)

        character = create_character(session, game, player, "Brave Knight")
        npc1 = create_npc(session, game, "Orc Warrior")
        npc2 = create_npc(session, game, "Orc Archer")

        encounter = create_encounter(session, game, status=EncounterStatus.READY)
        add_character_participant(session, encounter, character)
        add_npc_participant(session, encounter, npc1, instance_index=1)
        add_npc_participant(session, encounter, npc2, instance_index=1)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}/state",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()

        participants = data["encounter"]["participants"]
        assert len(participants) == 3

        # Check participant structure
        for p in participants:
            assert "id" in p
            assert "participant_type" in p
            assert "participant_id" in p
            assert "instance_index" in p

    def test_get_state_combatants_state_detail(
        self, client, session, cleanup_database
    ):
        """Test combatants_state contains expected fields."""
        dm = create_test_user(session, "dm@example.com", "DM User")

        game = create_game_with_dm(session, dm)
        encounter = create_encounter(session, game, status=EncounterStatus.ACTIVE)

        # Create state with detailed combatants
        state = EncounterState(
            encounter_id=encounter.id,
            current_round=2,
            current_turn_index=1,
            initiative_order=[
                {"key": "CHARACTER_1", "initiative": 20, "name": "Paladin"},
                {"key": "NPC_1_1", "initiative": 15, "name": "Dragon"},
            ],
            combatants_state={
                "CHARACTER_1": {
                    "name": "Paladin",
                    "current_hp": 45,
                    "max_hp": 60,
                    "temp_hp": 5,
                    "conditions": ["blessed", "inspired"],
                    "connection_status": "CONNECTED",
                    "disconnected_at": None,
                    "grace_period_ends": None,
                },
                "NPC_1_1": {
                    "name": "Dragon",
                    "current_hp": 150,
                    "max_hp": 200,
                    "conditions": ["frightening_presence"],
                    "connection_status": None,
                },
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

        combatants = data["state"]["combatants_state"]
        
        # Check character combatant
        char_state = combatants["CHARACTER_1"]
        assert char_state["current_hp"] == 45
        assert char_state["max_hp"] == 60
        assert char_state["temp_hp"] == 5
        assert "blessed" in char_state["conditions"]
        assert char_state["connection_status"] == "CONNECTED"

        # Check NPC combatant
        npc_state = combatants["NPC_1_1"]
        assert npc_state["current_hp"] == 150
        assert npc_state["max_hp"] == 200
        assert npc_state["connection_status"] is None

    def test_get_state_multiple_npc_instances(
        self, client, session, cleanup_database
    ):
        """Test encounter with multiple instances of same NPC."""
        dm = create_test_user(session, "dm@example.com", "DM User")

        game = create_game_with_dm(session, dm)
        goblin = create_npc(session, game, "Goblin")

        encounter = create_encounter(session, game, status=EncounterStatus.READY)
        # Add 3 goblins
        add_npc_participant(session, encounter, goblin, instance_index=1)
        add_npc_participant(session, encounter, goblin, instance_index=2)
        add_npc_participant(session, encounter, goblin, instance_index=3)
        session.commit()

        token = get_auth_token(client, "dm@example.com")
        response = client.get(
            f"/api/v1/game/{game.id}/encounter/{encounter.id}/state",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.get_json()

        participants = data["encounter"]["participants"]
        assert len(participants) == 3

        # All should reference the same NPC ID but different instance indices
        npc_id = goblin.id
        instance_indices = [p["instance_index"] for p in participants]
        assert sorted(instance_indices) == [1, 2, 3]
        assert all(p["participant_id"] == npc_id for p in participants)

