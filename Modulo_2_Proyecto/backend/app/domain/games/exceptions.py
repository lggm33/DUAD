"""
Domain exceptions for game operations.
"""


class GameDomainError(Exception):
    """Base exception for game domain."""
    pass


class GameNotFoundError(GameDomainError):
    """Raised when game is not found."""
    pass
