"""
Domain exceptions for game operations.
"""


class GameDomainError(Exception):
    """Base exception for game domain."""
    pass


class GameNotFoundError(GameDomainError):
    """Raised when game is not found."""
    pass


class GameAccessDeniedError(GameDomainError):
    """Raised when user doesn't have access to game or game resource."""
    pass


class GameValidationError(GameDomainError):
    """Raised when game validation fails."""
    pass


class GameStateError(GameDomainError):
    """Raised when game is in invalid state for operation."""
    pass


class GameInviteError(GameDomainError):
    """Raised when invite operation fails."""
    pass


class GameMembershipError(GameDomainError):
    """Raised when membership operation fails."""
    pass


class RulesetNotFoundError(GameDomainError):
    """Raised when ruleset template is not found."""
    pass


class RulesetAccessDeniedError(GameDomainError):
    """Raised when user doesn't have access to ruleset template."""
    pass
