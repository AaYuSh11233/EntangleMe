from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from contextlib import asynccontextmanager
import uvicorn
import os
from sqlalchemy import inspect, text
from pydantic import BaseModel
from pathlib import Path

from app.core.config import settings
from app.api import quantum, chat
from app.database.session import engine
from app.models.database import Base

# Request model for database reset
class ResetDatabaseRequest(BaseModel):
    confirmation: str

# Create database tables
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    
    # Reset database in production if RESET_DB environment variable is set
    if os.getenv("RESET_DB", "false").lower() == "true" or os.getenv("ENVIRONMENT") == "production":
        print(" Resetting database for production...")
        try:
            # Drop all tables and recreate them
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            print("✅ Database reset completed")
        except Exception as e:
            print(f"⚠️ Database reset failed: {e}")
    
    yield
    # Shutdown
    pass

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Quantum Teleportation Chat API - Secure messaging using quantum principles",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(quantum.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to EntangleME - Quantum Teleportation Chat API",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "health": "/health",
            "database_status": "/db-status",
            "reset_database": "/reset-db",
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "EntangleME Backend",
        "version": settings.VERSION
    }

# Reset database HTML page endpoint (GET)
@app.get("/reset-db", response_class=HTMLResponse)
async def reset_database_page():
    """
    Serve the reset database HTML page
    """
    try:
        # Get the path to the HTML file
        backend_dir = Path(__file__).parent.parent
        html_file_path = backend_dir / "reset-database.html"
        
        if not html_file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Reset database HTML page not found"
            )
        
        # Read and return the HTML content
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serve reset database page: {str(e)}"
        )

# Reset database endpoint (POST)
@app.post("/reset-db")
async def reset_database(request: ResetDatabaseRequest):
    """
    Reset the entire database - DANGER: This will delete all data!
    
    This endpoint will:
    - Drop all existing tables
    - Recreate all tables with fresh schema
    - Clear all user data, messages, and room information
    
    **Request Body:**
    ```json
    {
        "confirmation": "yes"
    }
    ```
    
    **⚠️ WARNING:** This will permanently delete ALL data in the database!
    Use with extreme caution.
    """
    try:
        # Check confirmation parameter
        if request.confirmation.lower() != "yes":
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "Confirmation required",
                    "message": "To reset the database, you must provide confirmation='yes' in the request body.",
                    "example": {
                        "confirmation": "yes"
                    },
                    "warning": "This operation will permanently delete all data!"
                }
            )
        
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        
        # Recreate all tables
        Base.metadata.create_all(bind=engine)
        
        return {
            "status": "success",
            "message": "Database reset completed successfully",
            "details": {
                "tables_dropped": True,
                "tables_recreated": True,
                "data_cleared": True
            },
            "warning": "All data has been permanently deleted!",
            "timestamp": "Reset completed at current time"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database reset failed: {str(e)}"
        )

# Database status endpoint - serves HTML page or JSON based on Accept header
@app.get("/db-status")
async def database_status_endpoint(request: Request):
    """
    Serve the database status HTML page or JSON data based on Accept header
    """
    # Check if the request wants HTML
    accept_header = request.headers.get("accept", "").lower()
    if "text/html" in accept_header or request.query_params.get("format") == "html":
        # Serve HTML page
        try:
            backend_dir = Path(__file__).parent.parent
            html_file_path = backend_dir / "database-status.html"
            
            if not html_file_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail="Database status HTML page not found"
                )
            
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            return HTMLResponse(content=html_content)
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to serve database status page: {str(e)}"
            )
    else:
        # Serve JSON data
        try:
            # Check if tables exist
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            # Get actual data from tables
            table_data = {}
            table_counts = {}
            
            for table in existing_tables:
                try:
                    with engine.connect() as conn:
                        # Get count
                        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = count_result.scalar()
                        table_counts[table] = count
                        
                        # Get actual data (limit to 50 records for performance)
                        if count > 0:
                            if table == "users":
                                # Get user data with specific fields
                                result = conn.execute(text(f"""
                                    SELECT id, username, email, is_online, last_seen, created_at 
                                    FROM {table} 
                                    ORDER BY created_at DESC 
                                    LIMIT 50
                                """))
                                data = [dict(row) for row in result.mappings()]
                            elif table == "rooms":
                                # Get room data
                                result = conn.execute(text(f"""
                                    SELECT id, name, created_by, created_at, last_activity 
                                    FROM {table} 
                                    ORDER BY created_at DESC 
                                    LIMIT 50
                                """))
                                data = [dict(row) for row in result.mappings()]
                            elif table == "messages":
                                # Get message data (limit content length using SQLite functions)
                                result = conn.execute(text(f"""
                                    SELECT id, room_id, sender_id, 
                                           CASE 
                                               WHEN length(content) > 100 THEN substr(content, 1, 100) || '...'
                                               ELSE content 
                                           END as content,
                                           quantum_state, status, created_at 
                                    FROM {table} 
                                    ORDER BY created_at DESC 
                                    LIMIT 50
                                """))
                                data = [dict(row) for row in result.mappings()]
                            elif table == "room_participants":
                                # Get room participant data
                                result = conn.execute(text(f"""
                                    SELECT id, room_id, user_id, joined_at 
                                    FROM {table} 
                                    ORDER BY joined_at DESC 
                                    LIMIT 50
                                """))
                                data = [dict(row) for row in result.mappings()]
                            else:
                                # Generic data for other tables
                                result = conn.execute(text(f"SELECT * FROM {table} LIMIT 50"))
                                data = [dict(row) for row in result.mappings()]
                            
                            # Convert datetime objects to strings for JSON serialization
                            for item in data:
                                for key, value in item.items():
                                    if hasattr(value, 'isoformat'):
                                        item[key] = value.isoformat()
                            
                            table_data[table] = data
                        else:
                            table_data[table] = []
                            
                except Exception as e:
                    table_counts[table] = f"Error: {str(e)}"
                    table_data[table] = []
            
            return {
                "status": "healthy",
                "tables": existing_tables,
                "table_counts": table_counts,
                "table_data": table_data,
                "database_url": settings.DATABASE_URL.split('/')[-1] if settings.DATABASE_URL else "unknown",
                "environment": os.getenv("ENVIRONMENT", "development")
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "database_url": settings.DATABASE_URL.split('/')[-1] if settings.DATABASE_URL else "unknown"
            }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
