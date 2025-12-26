"""
Unit test fixtures and configuration.

Unit tests should be fast and not require database or external dependencies.
"""
from __future__ import annotations

import pytest

# Import all SQLAlchemy models to ensure they are registered in the mapper
# This is required when creating model instances in tests, even for unit tests
# that mock repositories, because SQLAlchemy validates relationships on instantiation
from app.domain.users.models import User  # noqa: F401
from app.domain.auth.models import AuthRefreshToken  # noqa: F401
from app.domain.games.models import Game, GameMembership, GameInvite  # noqa: F401


# Add unit test specific fixtures here
# Example: mocks, simple data fixtures, etc.
