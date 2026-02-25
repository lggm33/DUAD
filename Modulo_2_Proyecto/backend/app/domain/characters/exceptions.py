"""
Domain exceptions for character operations.
"""


class CharacterDomainError(Exception):
    """Base exception for character domain."""
    pass


class CharacterNotFoundError(CharacterDomainError):
    """Raised when character is not found."""
    pass


class CharacterAccessDeniedError(CharacterDomainError):
    """Raised when user doesn't have access to character."""
    pass


class CharacterNotEditableError(CharacterDomainError):
    """Raised when trying to edit non-editable character."""
    pass


class InventoryItemNotFoundError(CharacterDomainError):
    """Raised when inventory item is not found."""
    pass
