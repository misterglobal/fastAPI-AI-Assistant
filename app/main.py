from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import asyncio
import os
import uvicorn
import httpx
from app.core.config import settings
from app.api.api_v1.api import api_router
from contextlib import asynccontextmanager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configure connection pool for high concurrency
# Each agent should handle 10+ concurrent calls
connection_pool_limits = httpx.Limits(
    max_connections=500,  # Overall connection limit
    max_keepalive_connections=100,  # Keep-alive connections
    keepalive_expiry=30.0  # Keep-alive expiry time in seconds
)

# Set up a shared httpx client for all integrations
httpx_client = httpx.AsyncClient(limits=connection_pool_limits, timeout=30.0)

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize resources
    logger.info("Starting up AI Phone Assistant API")
    
    # Create global httpx client for all integrations
    app.state.httpx_client = httpx_client
    
    # Initialize other resources that might be needed
    # Set environment variables if not set
    if not os.environ.get("ELEVENLABS_API_KEY"):
        logger.warning("ELEVENLABS_API_KEY not set in environment. Voice features may not work.")
        
    if not os.environ.get("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not set in environment. AI features may not work.")
        
    if not os.environ.get("TWILIO_ACCOUNT_SID") or not os.environ.get("TWILIO_AUTH_TOKEN"):
        logger.warning("Twilio credentials not set. Call and SMS features may not work.")
    
    yield
    
    # Shutdown: Clean up resources
    logger.info("Shutting down AI Phone Assistant API")
    await httpx_client.aclose()

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI Phone Assistant API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to AI Phone Assistant API"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": os.environ.get("ENVIRONMENT", "development")
    }

# Error handling middleware
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.exception(f"Unhandled exception: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please try again later."}
        )

# Run the application with uvicorn when executed directly
if __name__ == "__main__":
    # Increased the number of workers for handling concurrent requests
    # workers = min(os.cpu_count() * 2 + 1, 8)  # Common formula for worker count
    # For more concurrency, use more workers or consider running with --workers flag
    
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )