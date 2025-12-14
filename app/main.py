"""
FastAPI application factory and configuration
"""
import logging
import os
from typing import Optional
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    load_dotenv(env_file)

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import time

from app.database import init_db
from app.api.routes import pages_router
from app.schemas import ErrorResponse

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class AppConfig:
    """Application configuration"""
    APP_NAME = "LinkedIn Insights Microservice"
    APP_VERSION = "1.0.0"
    API_PREFIX = os.getenv('API_PREFIX', '/api')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=AppConfig.APP_NAME,
        version=AppConfig.APP_VERSION,
        description="A robust microservice for scraping and analyzing LinkedIn company pages",
        debug=AppConfig.DEBUG
    )
    
    logger.info("FastAPI application initializing...")
    
    # ==================== CORS ====================
    origins = os.getenv(
        'CORS_ORIGINS',
        '["http://localhost:3000", "http://localhost:8000"]'
    )
    
    import json
    try:
        origins_list = json.loads(origins)
    except:
        origins_list = ["http://localhost:3000", "http://localhost:8000"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    logger.info(f"CORS enabled for origins: {origins_list}")
    
    # ==================== Request/Response Middleware ====================
    
    @app.middleware("http")
    async def add_request_id_middleware(request: Request, call_next):
        """Add request ID and timing to all requests"""
        import uuid
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.start_time = time.time()
        
        response = await call_next(request)
        
        # Add response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(time.time() - request.state.start_time)
        
        return response
    
    # ==================== Exception Handlers ====================
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler"""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=exc)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error="Internal server error",
                details={"type": exc.__class__.__name__}
            ).dict()
        )
    
    # ==================== Routes ====================
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": AppConfig.ENVIRONMENT
        }
    
    # API version endpoint
    @app.get("/api/version")
    async def version():
        """Get API version"""
        return {
            "app": AppConfig.APP_NAME,
            "version": AppConfig.APP_VERSION,
            "environment": AppConfig.ENVIRONMENT
        }
    
    # Startup event to create database tables
    @app.on_event("startup")
    def startup_event():
        """Initialize database tables on startup"""
        try:
            init_db()
            logger.info("Database tables initialized on startup")
        except Exception as e:
            logger.error(f"Failed to initialize database on startup: {e}")
            raise
    
    # Include routers
    app.include_router(pages_router)
    
    logger.info(f"FastAPI application created in {AppConfig.ENVIRONMENT} mode")
    
    return app


# Create app instance
app = create_app()


# Custom OpenAPI schema
def custom_openapi():
    """Customize OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=AppConfig.APP_NAME,
        version=AppConfig.APP_VERSION,
        description="""
        ## Overview
        A robust microservice for scraping and analyzing LinkedIn company pages.
        
        ## Features
        - **Scraping**: Fetch company details, posts, and employees from LinkedIn
        - **Storage**: Store data in relational database with proper relationships
        - **Search & Filter**: Advanced filtering by follower count, industry, name
        - **Pagination**: All list endpoints support pagination
        - **Caching**: Redis-based caching with configurable TTL
        - **AI Insights**: Generate AI-powered summaries using OpenAI
        - **Cloud Storage**: Optional S3 integration for storing images
        
        ## Getting Started
        1. Check the health endpoint: `GET /health`
        2. Get available pages: `GET /api/pages`
        3. Scrape a new page: `POST /api/pages/scrape`
        4. Get page details: `GET /api/pages/{page_id}`
        5. Get page posts: `GET /api/pages/{page_id}/posts`
        
        ## Authentication
        Currently, no authentication is required. In production, implement API key or JWT.
        
        ## Rate Limiting
        Not implemented in this version. Add in production.
        """,
        routes=app.routes,
    )
    
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=AppConfig.DEBUG,
        log_level=os.getenv('LOG_LEVEL', 'INFO').lower()
    )
