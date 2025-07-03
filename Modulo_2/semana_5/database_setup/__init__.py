"""
Database Setup Package for Lyfter Car Rental System

This package contains all the database setup scripts:
- DatabaseConfig: Base class for database configuration (NEW)
- DatabaseSetup: Creates database and schema
- UsersSetup: Creates and populates users table
- AutomobilesSetup: Creates and populates automobiles table
- RentalsSetup: Creates rentals table with relationships
- run_complete_setup: Executes complete system setup
"""

from .database_config import DatabaseConfig
from .setup_database import DatabaseSetup
from .setup_users import UsersSetup
from .setup_automobiles import AutomobilesSetup
from .setup_rentals import RentalsSetup
from .setup_complete import run_complete_setup

__all__ = [
    'DatabaseConfig',
    'DatabaseSetup',
    'UsersSetup', 
    'AutomobilesSetup',
    'RentalsSetup',
    'run_complete_setup'
]

__version__ = '1.0.0'
__author__ = 'Lyfter Car Rental Team'
__description__ = 'Database setup package for Lyfter Car Rental System' 