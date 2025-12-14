"""
Database configuration and session management
"""
import os
from typing import Optional
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration"""
    
    def __init__(self):
        self.database_url = os.getenv(
            'DATABASE_URL',
            'mysql+pymysql://root:password@localhost:3306/linkedin_insights'
        )
        self.echo_sql = os.getenv('DEBUG', 'False').lower() == 'true'
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '5'))
        self.max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '10'))
    
    def get_engine(self):
        """Create and return SQLAlchemy engine"""
        if 'sqlite' in self.database_url:
            # SQLite uses NullPool
            engine = create_engine(
                self.database_url,
                echo=self.echo_sql,
                connect_args={'check_same_thread': False},
                poolclass=NullPool
            )
        else:
            # MySQL/PostgreSQL use QueuePool
            engine = create_engine(
                self.database_url,
                echo=self.echo_sql,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_pre_ping=True,  # Test connections before using
                pool_recycle=3600,    # Recycle connections after 1 hour
            )
        
        return engine


# Initialize database configuration
db_config = DatabaseConfig()

# Initialize engine and session factory
engine = None
SessionLocal = None

def _init_engine():
    """Initialize engine lazily"""
    global engine, SessionLocal
    if engine is None:
        engine = db_config.get_engine()
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine

# Call _init_engine immediately on import
_init_engine()

def get_db() -> Session:
    """
    Dependency for getting database session
    
    Usage in FastAPI routes:
    @app.get("/items")
    def get_items(db: Session = Depends(get_db)):
        ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_db_async():
    """
    Async dependency for getting database session
    
    Usage in FastAPI routes:
    @app.get("/items")
    async def get_items(db: Session = Depends(get_db_async)):
        ...
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        await db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        await db.close()


def init_db():
    """Initialize database - create all tables"""
    from app.models import Base
    
    _init_engine()  # Ensure engine is initialized
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


def drop_db():
    """Drop all tables - WARNING: Use only in development"""
    from app.models import Base
    
    _init_engine()  # Ensure engine is initialized
    
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except SQLAlchemyError as e:
        logger.error(f"Error dropping database tables: {str(e)}")
        raise


def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set SQLite pragmas for better performance"""
    if 'sqlite' in db_config.database_url:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Register event listener lazily when engine is created
def _register_pragma_listener():
    _init_engine()  # Ensure engine is initialized
    event.listens_for(engine, "connect")(set_sqlite_pragma)
