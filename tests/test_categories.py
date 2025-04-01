"""Tests for knowledge category management."""
import pytest
import tempfile
import os

import callisto
from callisto.models import KnowledgeCategory

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

class TestCategoryManagement:
    """Test category management functionality."""
    
    def test_default_categories(self, api):
        """Test default categories are created."""
        categories = api.get_knowledge_categories()
        
        category_names = [cat["category_name"] for cat in categories]
        
        # Check some default categories
        assert "location" in category_names
        assert "likes" in category_names
        assert "dislikes" in category_names
        
        # Check data types
        location_cat = next(cat for cat in categories if cat["category_name"] == "location")
        assert location_cat["data_type"] == "string"
        assert location_cat["is_personal"] == True
        
        likes_cat = next(cat for cat in categories if cat["category_name"] == "likes")
        assert likes_cat["data_type"] == "list"
        assert likes_cat["is_personal"] == False
    
    def test_create_category(self, api):
        """Test creating a new category."""
        result = api.create_knowledge_category(
            category_name="test_category",
            data_type="string",
            is_personal=False
        )
        
        assert result == True
        
        # Verify category exists
        categories = api.get_knowledge_categories()
        category_names = [cat["category_name"] for cat in categories]
        assert "test_category" in category_names
        
        # Get specific category
        test_cat = next(cat for cat in categories if cat["category_name"] == "test_category")
        assert test_cat["data_type"] == "string"
        assert test_cat["is_personal"] == False
    
    def test_create_duplicate_category(self, api):
        """Test creating a duplicate category returns False."""
        # Create first time
        api.create_knowledge_category(
            category_name="duplicate_category",
            data_type="string"
        )
        
        # Try to create again
        result = api.create_knowledge_category(
            category_name="duplicate_category",
            data_type="number"
        )
        
        assert result == False
    
    def test_update_category(self, api):
        """Test updating a category."""
        # Create category
        api.create_knowledge_category(
            category_name="update_category",
            data_type="string",
            is_personal=False
        )
        
        # Update category
        result = api.update_knowledge_category(
            category_name="update_category",
            data_type="number",
            is_personal=True
        )
        
        assert result == True
        
        # Verify changes
        categories = api.get_knowledge_categories()
        updated_cat = next(cat for cat in categories if cat["category_name"] == "update_category")
        assert updated_cat["data_type"] == "number"
        assert updated_cat["is_personal"] == True
    
    def test_update_nonexistent_category(self, api):
        """Test updating a non-existent category returns False."""
        result = api.update_knowledge_category(
            category_name="nonexistent",
            data_type="string"
        )
        
        assert result == False
    
    def test_partial_update_category(self, api):
        """Test partial update of a category (only data_type)."""
        # Create category
        api.create_knowledge_category(
            category_name="partial_update",
            data_type="string",
            is_personal=False
        )
        
        # Update only data_type
        result = api.update_knowledge_category(
            category_name="partial_update",
            data_type="number"
        )
        
        assert result == True
        
        # Verify changes
        categories = api.get_knowledge_categories()
        updated_cat = next(cat for cat in categories if cat["category_name"] == "partial_update")
        assert updated_cat["data_type"] == "number"
        assert updated_cat["is_personal"] == False  # Should remain unchanged
    
    def test_delete_category(self, api):
        """Test deleting a category."""
        # Create category
        api.create_knowledge_category(
            category_name="delete_category",
            data_type="string"
        )
        
        # Delete category
        result = api.delete_knowledge_category("delete_category")
        
        assert result == True
        
        # Verify it's gone
        categories = api.get_knowledge_categories()
        category_names = [cat["category_name"] for cat in categories]
        assert "delete_category" not in category_names
    
    def test_delete_nonexistent_category(self, api):
        """Test deleting a non-existent category returns False."""
        result = api.delete_knowledge_category("nonexistent")
        
        assert result == False
    
    def test_filter_personal_categories(self, api):
        """Test filtering out personal categories."""
        # Create test categories
        api.create_knowledge_category(
            category_name="personal_category",
            data_type="string",
            is_personal=True
        )
        
        api.create_knowledge_category(
            category_name="non_personal_category",
            data_type="string",
            is_personal=False
        )
        
        # Get all categories
        all_categories = api.get_knowledge_categories()
        all_names = [cat["category_name"] for cat in all_categories]
        assert "personal_category" in all_names
        assert "non_personal_category" in all_names
        
        # Get only non-personal categories
        non_personal = api.get_knowledge_categories(include_personal=False)
        non_personal_names = [cat["category_name"] for cat in non_personal]
        assert "personal_category" not in non_personal_names
        assert "non_personal_category" in non_personal_names