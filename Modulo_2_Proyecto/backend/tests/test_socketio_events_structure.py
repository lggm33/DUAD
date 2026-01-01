"""
Quick test to verify SocketIO event modules are properly structured.
"""

import pytest


class TestSocketIOModuleStructure:
    """Test that all SocketIO event modules import correctly and have proper structure."""

    def test_connection_events_imports(self):
        """Verify connection_events module imports correctly."""
        from app.realtime.connection_events import register_connection_events
        assert callable(register_connection_events)

    def test_game_room_events_imports(self):
        """Verify game_room_events module imports correctly."""
        from app.realtime.game_room_events import register_game_room_events
        assert callable(register_game_room_events)

    def test_chat_events_imports(self):
        """Verify chat_events module imports correctly."""
        from app.realtime.chat_events import register_chat_events
        assert callable(register_chat_events)

    def test_combat_events_imports(self):
        """Verify combat_events module imports correctly."""
        from app.realtime.combat_events import register_combat_events
        assert callable(register_combat_events)

    def test_main_orchestrator_imports(self):
        """Verify main socketio_events orchestrator imports correctly."""
        from app.realtime.socketio_events import register_socketio_events, authenticated_users
        assert callable(register_socketio_events)
        assert isinstance(authenticated_users, dict)

    def test_all_modules_registered_in_orchestrator(self):
        """Verify orchestrator imports all sub-modules."""
        import app.realtime.socketio_events as orchestrator
        
        # Check that orchestrator imports all register functions
        assert hasattr(orchestrator, 'register_connection_events')
        assert hasattr(orchestrator, 'register_game_room_events')
        assert hasattr(orchestrator, 'register_chat_events')
        assert hasattr(orchestrator, 'register_combat_events')

