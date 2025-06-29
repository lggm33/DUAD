"""
User endpoints for Lyfter Car Rental System
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from .models import UserCreate, UserResponse, UserStatusUpdate, SuccessResponse, ErrorResponse
from repositories.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["users"])
user_repo = UserRepository()

@router.post("/", response_model=UserResponse)
async def create_user(user_data: UserCreate):
    """Create a new user"""
    try:
        # Check if the user already exists
        if user_repo.user_exists(email=user_data.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        
        if user_repo.user_exists(username=user_data.username):
            raise HTTPException(status_code=400, detail="Username already in use")
        
        # Create the user
        result = user_repo.create_user(user_data.dict())
        
        if not result:
            raise HTTPException(status_code=500, detail="Error creating the user")
        
        return UserResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/", response_model=List[UserResponse])
async def list_users(
    username: Optional[str] = Query(None, description="Filtrar por username"),
    email: Optional[str] = Query(None, description="Filtrar por email"),
    account_state: Optional[bool] = Query(None, description="Filtrar por estado de cuenta"),
    limit: int = Query(50, ge=1, le=1000, description="Número de registros a retornar"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir")
):
    """List users with optional filters"""
    try:
        # Build filters
        filters = {}
        if username:
            filters['username'] = f"%{username}%"
        if email:
            filters['email'] = f"%{email}%"
        if account_state is not None:
            filters['account_state'] = account_state
        
        # Get users
        where_clause, params = user_repo.build_where_clause(filters)
        pagination_clause = user_repo.build_pagination_clause(limit, offset)
        
        query = f"""
            SELECT id, name, email, username, date_of_birth, account_state, created_at, updated_at
            FROM {user_repo.get_table_name(user_repo.table_name)}
            {where_clause}
            ORDER BY created_at DESC
            {pagination_clause}
        """
        
        users = user_repo.execute_query(query, tuple(params))
        return [UserResponse(**user) for user in users]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios: {str(e)}")

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get a user by ID"""
    try:
        user = user_repo.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(**user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuario: {str(e)}")

@router.put("/{user_id}/status", response_model=UserResponse)
async def update_user_status(user_id: int, status_data: UserStatusUpdate):
    """Update the account status of a user"""
    try:
        # Check if the user exists
        existing_user = user_repo.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update status
        updated_user = user_repo.update_user_status(user_id, status_data.account_state)
        
        if not updated_user:
            raise HTTPException(status_code=500, detail="Error updating the user's account status")
        
        return UserResponse(**updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating the user: {str(e)}")

@router.delete("/{user_id}", response_model=SuccessResponse)
async def delete_user(user_id: int):
    """Delete a user"""
    try:
        # Check if the user exists
        existing_user = user_repo.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete user
        success = user_repo.delete_user(user_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Error deleting the user")
        
        return SuccessResponse(message="User deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting the user: {str(e)}")

@router.get("/stats/summary")
async def get_user_stats():
    """Get user statistics"""
    try:
        stats = user_repo.get_user_stats()
        return {"stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user statistics: {str(e)}") 