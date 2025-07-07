"""
Pydantic models for request and response validation
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class AccountStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class AutomobileStatus(str, Enum):
    AVAILABLE = "available"
    RENTED = "rented"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"

class RentalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

# ============================================================================
# USER MODELS
# ============================================================================

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    username: str
    password: str
    date_of_birth: Optional[date] = None
    account_state: bool = True

    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('The name must have at least 2 characters')
        return v.strip()

    @validator('username')
    def validate_username(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('The username must have at least 3 characters')
        return v.strip()

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    username: str
    date_of_birth: Optional[date]
    account_state: bool
    created_at: datetime
    updated_at: datetime

class UserStatusUpdate(BaseModel):
    account_state: bool

# ============================================================================
# AUTOMOBILE MODELS
# ============================================================================

class AutomobileCreate(BaseModel):
    make: str
    model: str
    year_manufactured: int
    condition: str
    status: AutomobileStatus = AutomobileStatus.AVAILABLE

    @validator('year_manufactured')
    def validate_year(cls, v):
        current_year = datetime.now().year
        if v < 1900 or v > current_year + 1:
            raise ValueError(f'Year must be between 1900 and {current_year + 1}')
        return v

    @validator('make', 'model', 'condition')
    def validate_strings(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Must have at least 2 characters')
        return v.strip()

class AutomobileResponse(BaseModel):
    id: int
    make: str
    model: str
    year_manufactured: int
    condition: str
    status: str
    created_at: datetime
    updated_at: datetime

class AutomobileStatusUpdate(BaseModel):
    status: AutomobileStatus

# ============================================================================
# RENTAL MODELS
# ============================================================================

class RentalCreate(BaseModel):
    user_id: int
    automobile_id: int
    expected_return_date: date
    daily_rate: float
    total_cost: float

    @validator('daily_rate', 'total_cost')
    def validate_positive_amounts(cls, v):
        if v <= 0:
            raise ValueError('The amounts must be positive')
        return v

    @validator('expected_return_date')
    def validate_future_date(cls, v):
        if v <= date.today():
            raise ValueError('The return date must be in the future')
        return v

class RentalResponse(BaseModel):
    id: int
    user_id: int
    automobile_id: int
    rental_date: datetime
    expected_return_date: date
    actual_return_date: Optional[datetime]
    rental_status: str
    daily_rate: float
    total_cost: float
    created_at: datetime
    updated_at: datetime
    # Related data
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    automobile_make: Optional[str] = None
    automobile_model: Optional[str] = None
    automobile_year: Optional[int] = None

class RentalComplete(BaseModel):
    actual_return_date: Optional[datetime] = None

# ============================================================================
# RESPONSE MODELS
# ============================================================================

class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None

class PaginatedResponse(BaseModel):
    data: List[dict]
    total: int
    limit: int
    offset: int
    has_more: bool 