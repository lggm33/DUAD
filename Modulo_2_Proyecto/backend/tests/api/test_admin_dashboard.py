import pytest
from app.domain.users.models import User, UserRole
from app.domain.games.models import (
    Game,
    GameStatus,
    GameMembership,
    GameRoleInGame,
    GameMembershipStatus,
)
from app.utils.password_hasher import PasswordHasher

def create_test_user(session, email: str, name: str, username: str = None, role: str = UserRole.USER.value):
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
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    return login_resp.get_json()["access_token"]

def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}

def create_game_with_dm(session, dm_user: User, name: str = "Test Game"):
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
    membership = GameMembership(
        game_id=game.id,
        user_id=player.id,
        role_in_game=GameRoleInGame.PLAYER,
        status=GameMembershipStatus.ACTIVE,
    )
    session.add(membership)
    session.flush()
    return membership

class TestAdminDashboardAPI:
    def test_list_games_admin_only(self, client, session, cleanup_database):
        admin = create_test_user(session, "admin@example.com", "Admin", role=UserRole.ADMIN.value)
        user = create_test_user(session, "user@example.com", "User")
        create_game_with_dm(session, user, "Game 1")
        session.commit()
        
        # Admin can list
        admin_token = get_auth_token(client, "admin@example.com")
        resp = client.get("/api/v1/admin/games", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        assert len(resp.get_json()["games"]) >= 1
        
        # Regular user cannot
        user_token = get_auth_token(client, "user@example.com")
        resp = client.get("/api/v1/admin/games", headers=auth_headers(user_token))
        assert resp.status_code == 403

    def test_filter_games_by_status(self, client, session, cleanup_database):
        admin = create_test_user(session, "admin@example.com", "Admin", role=UserRole.ADMIN.value)
        dm = create_test_user(session, "dm@example.com", "DM")
        g1 = create_game_with_dm(session, dm, "Active Game")
        g2 = create_game_with_dm(session, dm, "Ended Game")
        g2.status = GameStatus.ENDED
        session.commit()
        
        admin_token = get_auth_token(client, "admin@example.com")
        
        # Filter ACTIVE
        resp = client.get("/api/v1/admin/games?status=ACTIVE", headers=auth_headers(admin_token))
        games = resp.get_json()["games"]
        assert all(g["status"] == "ACTIVE" for g in games)
        assert any(g["name"] == "Active Game" for g in games)
        
        # Filter ENDED
        resp = client.get("/api/v1/admin/games?status=ENDED", headers=auth_headers(admin_token))
        games = resp.get_json()["games"]
        assert all(g["status"] == "ENDED" for g in games)
        assert any(g["name"] == "Ended Game" for g in games)

    def test_end_game_admin(self, client, session, cleanup_database):
        admin = create_test_user(session, "admin@example.com", "Admin", role=UserRole.ADMIN.value)
        dm = create_test_user(session, "dm@example.com", "DM")
        game = create_game_with_dm(session, dm, "Game to End")
        session.commit()
        
        admin_token = get_auth_token(client, "admin@example.com")
        resp = client.post(f"/api/v1/admin/games/{game.id}/end", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        
        # Verify in DB
        session.expire_all()
        updated_game = session.get(Game, game.id)
        assert updated_game.status == GameStatus.ENDED

    def test_kick_player_admin(self, client, session, cleanup_database):
        admin = create_test_user(session, "admin@example.com", "Admin", role=UserRole.ADMIN.value)
        dm = create_test_user(session, "dm@example.com", "DM")
        player = create_test_user(session, "player@example.com", "Player")
        game = create_game_with_dm(session, dm, "Game with Player")
        add_player_to_game(session, game, player)
        session.commit()
        
        admin_token = get_auth_token(client, "admin@example.com")
        resp = client.post(f"/api/v1/admin/games/{game.id}/kick-member", 
                          json={"user_id": player.id}, 
                          headers=auth_headers(admin_token))
        assert resp.status_code == 200
        assert resp.get_json()["game_ended"] is False
        
        # Verify membership
        session.expire_all()
        membership = session.query(GameMembership).filter_by(game_id=game.id, user_id=player.id).first()
        assert membership.status == GameMembershipStatus.KICKED

    def test_kick_dm_ends_game(self, client, session, cleanup_database):
        admin = create_test_user(session, "admin@example.com", "Admin", role=UserRole.ADMIN.value)
        dm = create_test_user(session, "dm@example.com", "DM")
        game = create_game_with_dm(session, dm, "Game to End by Kick")
        session.commit()
        
        admin_token = get_auth_token(client, "admin@example.com")
        resp = client.post(f"/api/v1/admin/games/{game.id}/kick-member", 
                          json={"user_id": dm.id}, 
                          headers=auth_headers(admin_token))
        assert resp.status_code == 200
        assert resp.get_json()["game_ended"] is True
        
        # Verify game status
        session.expire_all()
        updated_game = session.get(Game, game.id)
        assert updated_game.status == GameStatus.ENDED

    def test_list_users_admin(self, client, session, cleanup_database):
        admin = create_test_user(session, "admin@example.com", "Admin", role=UserRole.ADMIN.value)
        create_test_user(session, "user1@example.com", "User 1")
        create_test_user(session, "user2@example.com", "User 2")
        session.commit()
        
        admin_token = get_auth_token(client, "admin@example.com")
        resp = client.get("/api/v1/admin/users", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        users = resp.get_json()["users"]
        assert len(users) >= 3 # admin + user1 + user2

    def test_list_games_search(self, client, session, cleanup_database):
        admin = create_test_user(session, "admin@example.com", "Admin", role=UserRole.ADMIN.value)
        dm = create_test_user(session, "dm@example.com", "DM")
        create_game_with_dm(session, dm, "Dragon Quest")
        create_game_with_dm(session, dm, "Space Adventure")
        session.commit()
        
        admin_token = get_auth_token(client, "admin@example.com")
        
        # Search "Dragon"
        resp = client.get("/api/v1/admin/games?search=Dragon", headers=auth_headers(admin_token))
        games = resp.get_json()["games"]
        assert len(games) == 1
        assert games[0]["name"] == "Dragon Quest"
        
        # Search "Adventure"
        resp = client.get("/api/v1/admin/games?search=Adventure", headers=auth_headers(admin_token))
        games = resp.get_json()["games"]
        assert len(games) == 1
        assert games[0]["name"] == "Space Adventure"
