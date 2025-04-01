"""Tests for database initialization and connection."""
import os
import pytest
import tempfile
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session

import callisto
from callisto.db import Database
from callisto.models import Base, Platform, KnowledgeCategory

class TestDatabase:
    """Test database initialization and operations."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    def test_init_with_path(self, temp_db_path):
        """Test database initialization with specific path."""
        db = Database(temp_db_path)
        assert isinstance(db.engine, Engine)
        assert os.path.exists(temp_db_path)
    
    def test_init_default(self):
        """Test database initialization with default path."""
        db = Database()
        assert isinstance(db.engine, Engine)
        home_dir = os.path.expanduser("~")
        default_path = os.path.join(home_dir, ".jupiter", "callisto.db")
        assert os.path.exists(default_path)
    
    def test_session_context(self, temp_db_path):
        """Test session context manager."""
        db = Database(temp_db_path)
        with db.session() as session:
            assert isinstance(session, Session)
    
    def test_init_db(self, temp_db_path):
        """Test database table creation."""
        db = Database(temp_db_path)
        db.init_db()
        
        # Check if tables were created by querying them
        with db.session() as session:
            platforms = session.query(Platform).all()
            assert isinstance(platforms, list)
    
    def test_init_default_data(self, temp_db_path):
        """Test initialization of default data."""
        db = Database(temp_db_path)
        db.init_db()
        db.init_default_data()
        
        with db.session() as session:
            # Check default platforms
            platforms = session.query(Platform).all()
            platform_names = [p.platform_name for p in platforms]
            assert "gui" in platform_names
            assert "discord" in platform_names
            assert "terminal" in platform_names
            
            # Check default categories
            categories = session.query(KnowledgeCategory).all()
            category_names = [c.category_name for c in categories]
            assert "location" in category_names
            assert "likes" in category_names
    
    def test_execute_atomic(self, temp_db_path):
        """Test atomic operation execution."""
        db = Database(temp_db_path)
        db.init_db()
        
        def add_platform(session, name):
            platform = Platform(platform_name=name)
            session.add(platform)
            return platform.platform_name
        
        # Execute operation atomically
        result = db.execute_atomic(add_platform, "test_platform")
        assert result == "test_platform"
        
        # Verify platform was added
        with db.session() as session:
            platform = session.query(Platform).filter_by(platform_name="test_platform").first()
            assert platform is not None
            assert platform.platform_name == "test_platform"
    
    def test_initialize_function(self, temp_db_path):
        """Test global initialize function."""
        db = callisto.initialize(temp_db_path)
        assert isinstance(db, Database)
        assert os.path.exists(temp_db_path)
        
        # Verify tables and default data
        with db.session() as session:
            platforms = session.query(Platform).all()
            assert len(platforms) > 0