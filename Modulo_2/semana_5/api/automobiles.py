"""
Automobile endpoints for Lyfter Car Rental System
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from .models import AutomobileCreate, AutomobileResponse, AutomobileStatusUpdate, SuccessResponse
from repositories.automobile_repository import AutomobileRepository

router = APIRouter(prefix="/automobiles", tags=["automobiles"])
automobile_repo = AutomobileRepository()

@router.post("/", response_model=AutomobileResponse)
async def create_automobile(automobile_data: AutomobileCreate):
    """Create a new automobile"""
    try:
        result = automobile_repo.create_automobile(automobile_data.dict())
        
        if not result:
            raise HTTPException(status_code=500, detail="Error creating the automobile")
        
        return AutomobileResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/", response_model=List[AutomobileResponse])
async def list_automobiles(
    make: Optional[str] = Query(None, description="Filter by make"),
    model: Optional[str] = Query(None, description="Filter by model"),
    year: Optional[int] = Query(None, description="Filter by year of manufacture"),
    status: Optional[str] = Query(None, description="Filter by status"),
    available_only: bool = Query(False, description="Show only available automobiles"),
    limit: int = Query(50, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """List automobiles with optional filters"""
    try:
        # If only available is requested, use the specific method
        if available_only:
            automobiles = automobile_repo.get_available_automobiles(limit, offset)
            return [AutomobileResponse(**auto) for auto in automobiles]
        
        # Build filters
        filters = {}
        if make:
            filters['make'] = f"%{make}%"
        if model:
            filters['model'] = f"%{model}%"
        if year:
            filters['year_manufactured'] = year
        if status:
            filters['status'] = status
        
        # Get automobiles
        where_clause, params = automobile_repo.build_where_clause(filters)
        pagination_clause = automobile_repo.build_pagination_clause(limit, offset)
        
        query = f"""
            SELECT id, make, model, year_manufactured, condition, status, created_at, updated_at
            FROM {automobile_repo.get_table_name(automobile_repo.table_name)}
            {where_clause}
            ORDER BY make, model
            {pagination_clause}
        """
        
        automobiles = automobile_repo.execute_query(query, tuple(params))
        return [AutomobileResponse(**auto) for auto in automobiles]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting automobiles: {str(e)}")

@router.get("/available", response_model=List[AutomobileResponse])
async def get_available_automobiles(
    limit: int = Query(50, ge=1, le=1000, description="Número de registros a retornar"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir")
):
    """Get all available automobiles for rent"""
    try:
        automobiles = automobile_repo.get_available_automobiles(limit, offset)
        return [AutomobileResponse(**auto) for auto in automobiles]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting available automobiles: {str(e)}")

@router.get("/rented", response_model=List[AutomobileResponse])
async def get_rented_automobiles(
    limit: int = Query(50, ge=1, le=1000, description="Número de registros a retornar"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir")
):
    """Get all currently rented automobiles"""
    try:
        automobiles = automobile_repo.get_rented_automobiles(limit, offset)
        return [AutomobileResponse(**auto) for auto in automobiles]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting rented automobiles: {str(e)}")

@router.get("/{automobile_id}", response_model=AutomobileResponse)
async def get_automobile(automobile_id: int):
    """Get an automobile by ID"""
    try:
        automobile = automobile_repo.get_automobile_by_id(automobile_id)
        
        if not automobile:
            raise HTTPException(status_code=404, detail="Automobile not found")
        
        return AutomobileResponse(**automobile)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting automobile: {str(e)}")

@router.put("/{automobile_id}/status", response_model=AutomobileResponse)
async def update_automobile_status(automobile_id: int, status_data: AutomobileStatusUpdate):
    """Update the status of an automobile"""
    try:
        # Check if the automobile exists
        existing_automobile = automobile_repo.get_automobile_by_id(automobile_id)
        if not existing_automobile:
            raise HTTPException(status_code=404, detail="Automobile not found")
        
        # Update status
        updated_automobile = automobile_repo.update_automobile_status(automobile_id, status_data.status.value)
        
        if not updated_automobile:
            raise HTTPException(status_code=500, detail="Error updating the automobile's status")
        
        return AutomobileResponse(**updated_automobile)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating automobile: {str(e)}")

@router.put("/{automobile_id}/disable", response_model=AutomobileResponse)
async def disable_automobile(automobile_id: int):
    """Disable an automobile (set status as retired)"""
    try:
        # Check if the automobile exists
        existing_automobile = automobile_repo.get_automobile_by_id(automobile_id)
        if not existing_automobile:
            raise HTTPException(status_code=404, detail="Automobile not found")
        
        # Disable automobile
        disabled_automobile = automobile_repo.disable_automobile(automobile_id)
        
        if not disabled_automobile:
            raise HTTPException(status_code=500, detail="Error disabling the automobile")
        
        return AutomobileResponse(**disabled_automobile)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error disabling automobile: {str(e)}")

@router.delete("/{automobile_id}", response_model=SuccessResponse)
async def delete_automobile(automobile_id: int):
    """Delete an automobile"""
    try:
        # Check if the automobile exists
        existing_automobile = automobile_repo.get_automobile_by_id(automobile_id)
        if not existing_automobile:
            raise HTTPException(status_code=404, detail="Automobile not found")
        
        # Delete automobile
        success = automobile_repo.delete_automobile(automobile_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Error deleting the automobile")
        
        return SuccessResponse(message="Automobile deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting automobile: {str(e)}")

@router.get("/stats/summary")
async def get_automobile_stats():
    """Get automobile statistics"""
    try:
        stats = automobile_repo.get_automobile_stats()
        return {"stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting automobile statistics: {str(e)}")

@router.get("/brands/models")
async def get_makes_and_models():
    """Get all makes and models"""
    try:
        makes_models = automobile_repo.get_makes_and_models()
        return {"makes_models": makes_models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting makes and models: {str(e)}") 