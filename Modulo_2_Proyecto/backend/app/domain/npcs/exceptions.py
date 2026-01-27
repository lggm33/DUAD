"""
Domain exceptions for NPC operations.
"""


class NPCDomainError(Exception):
    """Base exception for NPC domain."""
    pass


class NPCNotFoundError(NPCDomainError):
    """Raised when NPC is not found."""
    pass


class NPCAccessDeniedError(NPCDomainError):
    """Raised when user doesn't have access to NPC operations."""
    pass


class NPCValidationError(NPCDomainError):
    """Raised when NPC validation fails."""
    pass


class NPCStateError(NPCDomainError):
    """Raised when NPC is in invalid state for operation."""
    pass
