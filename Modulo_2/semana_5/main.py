#!/usr/bin/env python3
"""
Main application file for Lyfter Car Rental System
- Runs database setup on startup
- Provides FastAPI endpoints for the car rental system
"""

import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Import our complete setup module from database_setup package
from database_setup import run_complete_setup

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'lyfter_car_rental'),
}

SCHEMA_NAME = os.getenv('DB_SCHEMA', 'lyfter_car_rental')

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Runs setup on startup and cleanup on shutdown
    """
    print("🚀 Starting Lyfter Car Rental API...")
    
    # Run complete database setup on startup
    setup_success = run_complete_setup()
    
    if not setup_success:
        print("❌ Complete system setup failed. Exiting...")
        raise RuntimeError("Complete system setup failed")
    
    print("✅ Complete system setup completed successfully")
    print("🌐 API is ready to receive requests")
    
    yield  # This is where the application runs
    
    # Cleanup code (runs on shutdown)
    print("🔄 Shutting down Lyfter Car Rental API...")

# Create FastAPI app with lifespan manager
app = FastAPI(
    title="Lyfter Car Rental API",
    description="Complete car rental management system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection helper
def get_db_connection():
    """Get database connection with error handling"""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=int(DB_CONFIG['port']),
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        conn.autocommit = True
        return conn
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

def get_db_cursor(conn):
    """Get database cursor with RealDictCursor for JSON-like results"""
    return conn.cursor(cursor_factory=RealDictCursor)

# ============================================================================
# ROOT AND HEALTH ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Lyfter Car Rental API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "users": "/users",
            "automobiles": "/automobiles", 
            "rentals": "/rentals",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = get_db_cursor(conn)
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2024-01-01T00:00:00Z"  # In production, use actual timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# ============================================================================
# INCLUDE API ROUTERS
# ============================================================================

# Import and include API routers
from api import users_router, automobiles_router, rentals_router

app.include_router(users_router)
app.include_router(automobiles_router) 
app.include_router(rentals_router)

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function to run the API server"""
    print("🚀 Starting Lyfter Car Rental API Server")
    print("📋 Available endpoints will be visible at: http://localhost:8000/docs")
    print("🔗 API root: http://localhost:8000/")
    
    # Run the FastAPI server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )

if __name__ == "__main__":
    main() 