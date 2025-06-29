"""
API Package for Lyfter Car Rental System
Contains organized endpoints for users, automobiles, and rentals
"""

try:
    from .users import router as users_router
    from .automobiles import router as automobiles_router  
    from .rentals import router as rentals_router
    
    __all__ = ["users_router", "automobiles_router", "rentals_router"]
except ImportError:
    # Handle case where dependencies are not installed
    pass 