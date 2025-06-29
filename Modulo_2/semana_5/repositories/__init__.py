"""
Repositories Package for Lyfter Car Rental System

This package implements the Repository pattern for data access:
- BaseRepository: Common database operations
- UserRepository: User-specific operations
- AutomobileRepository: Automobile-specific operations  
- RentalRepository: Rental-specific operations
"""

from .base_repository import BaseRepository
from .user_repository import UserRepository
from .automobile_repository import AutomobileRepository
from .rental_repository import RentalRepository

__all__ = [
    'BaseRepository',
    'UserRepository',
    'AutomobileRepository', 
    'RentalRepository'
]

__version__ = '1.0.0'
__author__ = 'Lyfter Car Rental Team'
__description__ = 'Repository pattern implementation for Lyfter Car Rental System' 