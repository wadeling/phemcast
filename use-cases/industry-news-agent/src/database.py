"""Database connection manager for industry news agent."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
import os
from typing import Optional


class DatabaseManager:
    """Database connection manager."""
    
    def __init__(self):
        self.engine = None
        self.async_engine = None
        self.SessionLocal = None
        self.AsyncSessionLocal = None
    
    def init_database(self, database_url: str):
        """Initialize database connection."""
        # Sync engine for migrations - use PyMySQL
        if database_url.startswith('mysql://'):
            sync_url = database_url.replace('mysql://', 'mysql+pymysql://')
        else:
            sync_url = database_url
            
        self.engine = create_engine(sync_url)
        
        # Async engine for operations
        if database_url.startswith('mysql://'):
            async_url = database_url.replace('mysql://', 'mysql+aiomysql://')
        else:
            async_url = database_url.replace('mysql+pymysql://', 'mysql+aiomysql://')
            
        self.async_engine = create_async_engine(async_url)
        
        # Create tables
        # Import all models to ensure they're registered with Base
        from db_models import Base
        Base.metadata.create_all(bind=self.engine)
        
        # Session factories
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.AsyncSessionLocal = async_sessionmaker(
            self.async_engine, class_=AsyncSession, expire_on_commit=False
        )
    
    def get_session(self):
        """Get database session."""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()
    
    async def get_async_session(self):
        """Get async database session."""
        if not self.AsyncSessionLocal:
            raise RuntimeError("Database not initialized")
        return self.AsyncSessionLocal()
    
    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
        if self.async_engine:
            self.async_engine.dispose()


# Global database manager instance
db_manager = DatabaseManager()


def init_db(database_url: str):
    """Initialize database with retry mechanism."""
    import time
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            print(f"Attempting to connect to database (attempt {attempt + 1}/{max_retries})...")
            db_manager.init_database(database_url)
            print("Database connection established successfully!")
            return
        except Exception as e:
            print(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("Max retries reached. Database initialization failed.")
                raise


def get_db():
    """Get database session."""
    return db_manager.get_session()


async def get_async_db():
    """Get async database session."""
    if not db_manager.AsyncSessionLocal:
        raise RuntimeError("Database not initialized")
    return db_manager.AsyncSessionLocal()
