"""Database connection and session management for Callisto."""
import os
import json
from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from .models import Base

class Database:
    """Database connection manager with connection pooling and transactions."""
    
    def __init__(self, db_path: str = None):
        """Initialize database connection."""
        if not db_path:
            # Default to database in user's home directory
            home_dir = os.path.expanduser("~")
            jupiter_dir = os.path.join(home_dir, ".jupiter")
            os.makedirs(jupiter_dir, exist_ok=True)
            db_path = os.path.join(jupiter_dir, "callisto.db")
        
        # Create engine with connection pooling
        self.engine = create_engine(
            f"sqlite:///{db_path}", 
            poolclass=QueuePool,
            pool_pre_ping=True,  # Verify connections before using them
            pool_size=5,
            max_overflow=10,
            connect_args={"check_same_thread": False}
        )
        
        self.Session = sessionmaker(bind=self.engine)
    
    def init_db(self) -> None:
        """Create all tables if they don't exist."""
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Provide a transactional scope around operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def execute_atomic(self, operation, *args, **kwargs):
        """Execute an operation atomically within a transaction."""
        with self.session() as session:
            return operation(session, *args, **kwargs)
            
    def init_default_data(self) -> None:
        """Initialize default data like platforms and knowledge categories."""
        # Default platforms
        default_platforms = [
            {"platform_name": "gui"},
            {"platform_name": "discord"},
            {"platform_name": "terminal"},
        ]
        
        # Default knowledge categories
        default_categories = [
            {"category_name": "location", "data_type": "string", "is_personal": True},
            {"category_name": "likes", "data_type": "list", "is_personal": False},
            {"category_name": "dislikes", "data_type": "list", "is_personal": False},
            {"category_name": "birthday", "data_type": "date", "is_personal": True},
            {"category_name": "occupation", "data_type": "string", "is_personal": False},
        ]
        
        from .models import Platform, KnowledgeCategory
        
        with self.session() as session:
            # Add platforms if they don't exist
            for platform_data in default_platforms:
                platform_name = platform_data["platform_name"]
                existing = session.query(Platform).filter_by(platform_name=platform_name).first()
                if not existing:
                    platform = Platform(**platform_data)
                    session.add(platform)
            
            # Add knowledge categories if they don't exist
            for category_data in default_categories:
                category_name = category_data["category_name"]
                existing = session.query(KnowledgeCategory).filter_by(category_name=category_name).first()
                if not existing:
                    category = KnowledgeCategory(**category_data)
                    session.add(category)

# Global database instance
db = Database()
