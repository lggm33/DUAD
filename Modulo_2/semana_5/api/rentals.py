"""
Rental endpoints for Lyfter Car Rental System
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from .models import RentalCreate, RentalResponse, RentalComplete, SuccessResponse
from repositories.rental_repository import RentalRepository
from repositories.user_repository import UserRepository
from repositories.automobile_repository import AutomobileRepository

router = APIRouter(prefix="/rentals", tags=["rentals"])
rental_repo = RentalRepository()
user_repo = UserRepository()
automobile_repo = AutomobileRepository()

@router.post("/", response_model=RentalResponse)
async def create_rental(rental_data: RentalCreate):
    """Create a new rental"""
    try:
        # Check if the user exists and is active
        user = user_repo.get_user_by_id(rental_data.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if the automobile exists and is available
        automobile = automobile_repo.get_automobile_by_id(rental_data.automobile_id)
        if not automobile:
            raise HTTPException(status_code=404, detail="Automobile not found")
        if automobile['status'] != 'available':
            raise HTTPException(status_code=400, detail="Automobile not available")
        
        # Create the rental
        result = rental_repo.create_rental(rental_data.dict())
        
        if not result:
            raise HTTPException(status_code=500, detail="Error creating the rental")
        
        # Update the automobile status to 'rented'
        automobile_repo.update_automobile_status(rental_data.automobile_id, 'rented')
        
        return RentalResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/", response_model=List[RentalResponse])
async def list_rentals(
    user_id: Optional[int] = Query(None, description="Filtrar por ID de usuario"),
    automobile_id: Optional[int] = Query(None, description="Filtrar por ID de automóvil"),
    status: Optional[str] = Query(None, description="Filtrar por estado de renta"),
    date_from: Optional[str] = Query(None, description="Filtrar rentas desde fecha (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filtrar rentas hasta fecha (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=1000, description="Número de registros a retornar"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir")
):
    """List rentals with optional filters"""
    try:
        # Build filters
        filters = {}
        if user_id:
            filters['r.user_id'] = user_id
        if automobile_id:
            filters['r.automobile_id'] = automobile_id
        if status:
            filters['r.rental_status'] = status
        
        # Build base query
        where_clause, params = rental_repo.build_where_clause(filters)
        pagination_clause = rental_repo.build_pagination_clause(limit, offset)
        
        # Add date filters
        date_conditions = []
        if date_from:
            date_conditions.append("r.rental_date >= %s")
            params.append(date_from)
        if date_to:
            date_conditions.append("r.rental_date <= %s")
            params.append(date_to)
        
        if date_conditions:
            if where_clause:
                where_clause += " AND " + " AND ".join(date_conditions)
            else:
                where_clause = " WHERE " + " AND ".join(date_conditions)
        
        query = f"""
            SELECT 
                r.id, r.user_id, r.automobile_id, r.rental_date, r.expected_return_date,
                r.actual_return_date, r.rental_status, r.daily_rate, r.total_cost,
                r.created_at, r.updated_at,
                u.name as user_name, u.email as user_email,
                a.make as automobile_make, a.model as automobile_model,
                a.year_manufactured as automobile_year
            FROM {rental_repo.get_table_name(rental_repo.table_name)} r
            LEFT JOIN {rental_repo.get_table_name('users')} u ON r.user_id = u.id
            LEFT JOIN {rental_repo.get_table_name('automobiles')} a ON r.automobile_id = a.id
            {where_clause}
            ORDER BY r.rental_date DESC
            {pagination_clause}
        """
        
        rentals = rental_repo.execute_query(query, tuple(params))
        return [RentalResponse(**rental) for rental in rentals]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting rentals: {str(e)}")

@router.get("/active", response_model=List[RentalResponse])
async def get_active_rentals(
    limit: int = Query(50, ge=1, le=1000, description="Número de registros a retornar"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir")
):
    """Get all active rentals"""
    try:
        rentals = rental_repo.get_active_rentals(limit, offset)
        return [RentalResponse(**rental) for rental in rentals]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting active rentals: {str(e)}")

@router.get("/overdue", response_model=List[RentalResponse])
async def get_overdue_rentals(
    limit: int = Query(50, ge=1, le=1000, description="Número de registros a retornar"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir")
):
    """Get all overdue rentals"""
    try:
        rentals = rental_repo.get_overdue_rentals(limit, offset)
        return [RentalResponse(**rental) for rental in rentals]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting overdue rentals: {str(e)}")

@router.get("/{rental_id}", response_model=RentalResponse)
async def get_rental(rental_id: int):
    """Get a rental by ID"""
    try:
        rental = rental_repo.get_rental_by_id(rental_id)
        
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        
        return RentalResponse(**rental)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting rental: {str(e)}")

@router.put("/{rental_id}/complete", response_model=RentalResponse)
async def complete_rental(rental_id: int, completion_data: RentalComplete = RentalComplete()):
    """Complete a rental (return of the automobile)"""
    try:
        # Check if the rental exists and is active
        existing_rental = rental_repo.get_rental_by_id(rental_id)
        if not existing_rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        if existing_rental['rental_status'] != 'active':
            raise HTTPException(status_code=400, detail="Rental not active")
        
        
        completed_rental = rental_repo.complete_rental(
            rental_id, 
            completion_data.actual_return_date or datetime.now()
        )
        
        if not completed_rental:
            raise HTTPException(status_code=500, detail="Error completing the rental")
        
        # Get the completed rental details
        rental_details = rental_repo.get_rental_by_id(rental_id)
        if not rental_details:
            raise HTTPException(status_code=404, detail="Could not get the completed rental details")
        return RentalResponse(**rental_details)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing the rental: {str(e)}")

@router.delete("/{rental_id}", response_model=SuccessResponse)
async def delete_rental(rental_id: int):
    """Delete a rental (only if it is cancelled or completed)"""
    try:
        # Check if the rental exists
        existing_rental = rental_repo.get_rental_by_id(rental_id)
        if not existing_rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        
        # Check if the rental can be deleted
        if existing_rental['rental_status'] not in ['cancelled', 'completed']:
            raise HTTPException(
                status_code=400, 
                detail="Only cancelled or completed rentals can be deleted"
            )
        
        # Delete rental
        success = rental_repo.delete_rental(rental_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Error deleting the rental")
        
        return SuccessResponse(message="Rental deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting the rental: {str(e)}")

@router.get("/stats/summary")
async def get_rental_stats():
    """Get rental statistics"""
    try:
        stats = rental_repo.get_rental_stats()
        return {"stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting rental statistics: {str(e)}") 