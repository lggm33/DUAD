class NoteDomainError(Exception):
    """Base exception for notes domain"""
    pass

class NoteNotFoundError(NoteDomainError):
    """Raised when note is not found"""
    pass

class NoteAccessDeniedError(NoteDomainError):
    """Raised when user doesn't have access to note"""
    pass

class NoteValidationError(NoteDomainError):
    """Raised when note validation fails"""
    pass
