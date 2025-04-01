"""Tests for user management functionality."""
import pytest
import tempfile
import os

import callisto
from callisto.models import User, Platform, UserPlatform

@pytest.fixture
def db_path():
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)

@pytest.fixture
def api(db_path):
    """Initialize API with test database."""
    callisto.initialize(db_path)
    from callisto.api import api
    return api

class TestUserManagement:
    """Test user management functionality."""
    
    def test_create_user(self, api):
        """Test user creation."""
        user = api.create_user(
            name="Test User",
            platform_name="terminal",
            platform_username="testuser"
        )
        
        assert user is not None
        assert user.name == "Test User"
        assert user.user_id is not None
    
    def test_get_user(self, api):
        """Test retrieving a user."""
        # Create user first
        created_user = api.create_user(
            name="Get Test",
            platform_name="discord",
            platform_username="gettest"
        )
        
        # Then retrieve it
        retrieved_user = api.get_user("discord", "gettest")
        
        assert retrieved_user is not None
        assert retrieved_user.user_id == created_user.user_id
        assert retrieved_user.name == "Get Test"
    
    def test_get_nonexistent_user(self, api):
        """Test retrieving a non-existent user."""
        user = api.get_user("nonexistent", "nobody")
        assert user is None
    
    def test_update_user(self, api):
        """Test updating user information."""
        # Create user first
        user = api.create_user(
            name="Update Test",
            platform_name="terminal",
            platform_username="updatetest"
        )
        
        # Update the user
        api.update_user(user.user_id, "Updated Name")
        
        # Retrieve and verify
        updated_user = api.get_user("terminal", "updatetest")
        assert updated_user is not None
        assert updated_user.name == "Updated Name"
    
    def test_link_platform(self, api):
        """Test linking a user to a new platform."""
        # Create user first
        user = api.create_user(
            name="Link Test",
            platform_name="terminal",
            platform_username="linktest"
        )
        
        # Link to a new platform
        api.link_platform(
            user_id=user.user_id,
            platform_name="discord",
            platform_username="linktest_discord"
        )
        
        # Verify user can be retrieved via new platform
        retrieved_user = api.get_user("discord", "linktest_discord")
        assert retrieved_user is not None
        assert retrieved_user.user_id == user.user_id
    
    def test_delete_user(self, api):
        """Test user deletion."""
        # Create user first
        user = api.create_user(
            name="Delete Test",
            platform_name="terminal",
            platform_username="deletetest"
        )
        
        # Delete the user
        api.delete_user(user.user_id)
        
        # Verify user no longer exists
        deleted_user = api.get_user("terminal", "deletetest")
        assert deleted_user is None