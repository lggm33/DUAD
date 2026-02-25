import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from app.domain.games.game_service import GameService
from app.domain.games.models import (
    Game,
    GameInvite,
    GameRoleInGame,
    GameMembership,
    GameMembershipStatus,
    GameStatus,
)
from app.domain.games.game_repository import GameRepository
from app.domain.games.game_invites_repository import GameInvitesRepository
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.users.user_repository import UserRepository
from app.domain.users.models import User


@pytest.fixture
def mock_game_repo():
    return MagicMock(spec=GameRepository)


@pytest.fixture
def mock_invite_repo():
    return MagicMock(spec=GameInvitesRepository)


@pytest.fixture
def mock_membership_repo():
    return MagicMock(spec=GameMembershipRepository)


@pytest.fixture
def mock_user_repo():
    return MagicMock(spec=UserRepository)


@pytest.fixture
def game_service(mock_game_repo, mock_invite_repo, mock_membership_repo, mock_user_repo):
    return GameService(
        game_repository=mock_game_repo,
        game_invites_repository=mock_invite_repo,
        game_membership_repository=mock_membership_repo,
        user_repository=mock_user_repo,
    )


def test_create_game_success(game_service, mock_game_repo, mock_invite_repo, mock_membership_repo, mock_user_repo):
    # Setup
    dm_user_id = 1
    game_name = "Epic Adventure"
    mock_user_repo.get_by_id.return_value = User(id=dm_user_id)
    mock_game_repo.get_game_by_dm_user_id.return_value = None
    
    created_game = Game(id=1, name=game_name, dm_user_id=dm_user_id, status=GameStatus.ACTIVE)
    mock_game_repo.create_game.return_value = created_game
    
    # Execute
    result = game_service.create_game(game_name, dm_user_id)
    
    # Assert
    assert result["game"].name == game_name
    assert result["game"].dm_user_id == dm_user_id
    assert result["game_invite"].game_id == created_game.id
    
    mock_user_repo.get_by_id.assert_called_once_with(dm_user_id)
    mock_game_repo.create_game.assert_called_once()
    mock_membership_repo.create_game_membership.assert_called_once()
    mock_invite_repo.create_game_invite.assert_called_once()


def test_create_game_user_not_found(game_service, mock_user_repo):
    # Setup
    mock_user_repo.get_by_id.return_value = None
    
    # Execute & Assert
    with pytest.raises(ValueError, match="DM user not found"):
        game_service.create_game("Test Game", 999)


def test_create_game_already_dm_active(game_service, mock_user_repo, mock_game_repo):
    # Setup
    dm_user_id = 1
    mock_user_repo.get_by_id.return_value = User(id=dm_user_id)
    mock_game_repo.get_game_by_dm_user_id.return_value = Game(
        id=1, dm_user_id=dm_user_id, status=GameStatus.ACTIVE
    )
    
    # Execute & Assert
    with pytest.raises(ValueError, match="DM user is already a DM of another active game"):
        game_service.create_game("Another Game", dm_user_id)


def test_join_game_success_new_member(game_service, mock_game_repo, mock_membership_repo):
    # Setup
    game_id = 1
    user_id = 2
    mock_game_repo.get_game_by_id.return_value = Game(id=game_id, status=GameStatus.ACTIVE)
    mock_membership_repo.get_game_membership_by_game_id_and_user_id.return_value = None
    
    expected_membership = GameMembership(
        game_id=game_id, user_id=user_id, role_in_game=GameRoleInGame.PLAYER, status=GameMembershipStatus.ACTIVE
    )
    mock_membership_repo.create_game_membership.return_value = expected_membership
    
    # Execute
    result = game_service.join_game(game_id, user_id)
    
    # Assert
    assert result.game_id == game_id
    assert result.user_id == user_id
    assert result.status == GameMembershipStatus.ACTIVE
    mock_membership_repo.create_game_membership.assert_called_once()


def test_join_game_success_reactivate(game_service, mock_game_repo, mock_membership_repo):
    # Setup
    game_id = 1
    user_id = 2
    mock_game_repo.get_game_by_id.return_value = Game(id=game_id, status=GameStatus.ACTIVE)
    
    existing_membership = GameMembership(
        game_id=game_id, user_id=user_id, status=GameMembershipStatus.LEFT
    )
    mock_membership_repo.get_game_membership_by_game_id_and_user_id.return_value = existing_membership
    
    # Execute
    result = game_service.join_game(game_id, user_id)
    
    # Assert
    assert result.status == GameMembershipStatus.ACTIVE
    assert result.left_at is None
    mock_membership_repo.create_game_membership.assert_not_called()


def test_join_game_not_found(game_service, mock_game_repo):
    # Setup
    mock_game_repo.get_game_by_id.return_value = None
    
    # Execute & Assert
    with pytest.raises(ValueError, match="Game not found"):
        game_service.join_game(999, 1)


def test_join_game_not_active(game_service, mock_game_repo):
    # Setup
    mock_game_repo.get_game_by_id.return_value = Game(id=1, status=GameStatus.ENDED)
    
    # Execute & Assert
    with pytest.raises(ValueError, match="Game is not active"):
        game_service.join_game(1, 1)


def test_join_game_already_active_member(game_service, mock_game_repo, mock_membership_repo):
    # Setup
    game_id = 1
    user_id = 1
    mock_game_repo.get_game_by_id.return_value = Game(id=game_id, status=GameStatus.ACTIVE)
    mock_membership_repo.get_game_membership_by_game_id_and_user_id.return_value = GameMembership(
        game_id=game_id, user_id=user_id, status=GameMembershipStatus.ACTIVE
    )
    
    # Execute & Assert
    with pytest.raises(ValueError, match="User is already an active member of the game"):
        game_service.join_game(game_id, user_id)


def test_leave_game_success(game_service, mock_game_repo, mock_membership_repo):
    # Setup
    game_id = 1
    user_id = 1
    mock_game_repo.get_game_by_id.return_value = Game(id=game_id)
    membership = GameMembership(game_id=game_id, user_id=user_id, status=GameMembershipStatus.ACTIVE)
    mock_membership_repo.get_game_membership_by_game_id_and_user_id.return_value = membership
    
    # Execute
    result = game_service.leave_game(game_id, user_id)
    
    # Assert
    assert result is True
    assert membership.status == GameMembershipStatus.LEFT
    assert membership.left_at is not None


def test_leave_game_not_found(game_service, mock_game_repo):
    # Setup
    mock_game_repo.get_game_by_id.return_value = None
    
    # Execute & Assert
    with pytest.raises(ValueError, match="Game not found"):
        game_service.leave_game(999, 1)


def test_leave_game_not_active_member(game_service, mock_game_repo, mock_membership_repo):
    # Setup
    game_id = 1
    user_id = 1
    mock_game_repo.get_game_by_id.return_value = Game(id=game_id)
    
    # Case 1: No membership
    mock_membership_repo.get_game_membership_by_game_id_and_user_id.return_value = None
    with pytest.raises(ValueError, match="User is not an active member of the game"):
        game_service.leave_game(game_id, user_id)
        
    # Case 2: Membership status is already LEFT
    mock_membership_repo.get_game_membership_by_game_id_and_user_id.return_value = GameMembership(
        game_id=game_id, user_id=user_id, status=GameMembershipStatus.LEFT
    )
    with pytest.raises(ValueError, match="User is not an active member of the game"):
        game_service.leave_game(game_id, user_id)

