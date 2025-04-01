"""Tests for knowledge storage and retrieval functionality."""
import pytest
import tempfile
import os
import time

import callisto
from callisto.models import User, KnowledgeCategory, UserKnowledge

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

@pytest.fixture
def test_user(api):
    """Create a test user."""
    user = api.create_user(
        name="Knowledge Test",
        platform_name="terminal",
        platform_username="knowledgetest"
    )
    return user

class TestKnowledgeManagement:
    """Test knowledge management functionality."""
    
    def test_store_and_retrieve_string(self, api, test_user):
        """Test storing and retrieving string knowledge."""
        api.store_knowledge(
            user_id=test_user.user_id,
            category_name="test_string",
            value="Test Value",
            confidence=1.0,
            source="user_stated"
        )
        
        # Retrieve knowledge
        knowledge = api.get_user_knowledge(test_user.user_id)
        
        assert "test_string" in knowledge
        assert knowledge["test_string"]["value"] == "Test Value"
        assert knowledge["test_string"]["confidence"] == 1.0
        assert knowledge["test_string"]["source"] == "user_stated"
    
    def test_store_and_retrieve_list(self, api, test_user):
        """Test storing and retrieving list knowledge."""
        test_list = ["item1", "item2", "item3"]
        
        api.store_knowledge(
            user_id=test_user.user_id,
            category_name="test_list",
            value=test_list,
            confidence=0.8,
            source="extracted"
        )
        
        # Retrieve knowledge
        knowledge = api.get_user_knowledge(test_user.user_id)
        
        assert "test_list" in knowledge
        assert isinstance(knowledge["test_list"]["value"], list)
        assert knowledge["test_list"]["value"] == test_list
        assert knowledge["test_list"]["confidence"] == 0.8
        assert knowledge["test_list"]["source"] == "extracted"
    
    def test_update_knowledge(self, api, test_user):
        """Test updating existing knowledge."""
        # Store initial knowledge
        api.store_knowledge(
            user_id=test_user.user_id,
            category_name="update_test",
            value="Initial Value",
            confidence=0.5
        )
        
        # Update with higher confidence
        api.store_knowledge(
            user_id=test_user.user_id,
            category_name="update_test",
            value="Updated Value",
            confidence=0.8
        )
        
        # Retrieve knowledge
        knowledge = api.get_user_knowledge(test_user.user_id)
        
        assert knowledge["update_test"]["value"] == "Updated Value"
        assert knowledge["update_test"]["confidence"] == 0.8
    
    def test_knowledge_not_updated_with_lower_confidence(self, api, test_user):
        """Test knowledge not updated with lower confidence."""
        # Store initial knowledge with high confidence
        api.store_knowledge(
            user_id=test_user.user_id,
            category_name="confidence_test",
            value="High Confidence Value",
            confidence=0.9
        )
        
        # Try to update with lower confidence
        api.store_knowledge(
            user_id=test_user.user_id,
            category_name="confidence_test",
            value="Low Confidence Value",
            confidence=0.3
        )
        
        # Retrieve knowledge
        knowledge = api.get_user_knowledge(test_user.user_id)
        
        # Should still have the high confidence value
        assert knowledge["confidence_test"]["value"] == "High Confidence Value"
        assert knowledge["confidence_test"]["confidence"] == 0.9
    
    def test_batch_store_knowledge(self, api, test_user):
        """Test batch storage of knowledge."""
        items = [
            {
                "category": "batch_item1",
                "value": "Batch Value 1",
                "confidence": 0.7,
                "source": "user_stated"
            },
            {
                "category": "batch_item2",
                "value": ["batch", "list", "items"],
                "confidence": 0.6,
                "source": "extracted"
            }
        ]
        
        api.batch_store_knowledge(test_user.user_id, items)
        
        # Retrieve knowledge
        knowledge = api.get_user_knowledge(test_user.user_id)
        
        assert "batch_item1" in knowledge
        assert "batch_item2" in knowledge
        assert knowledge["batch_item1"]["value"] == "Batch Value 1"
        assert knowledge["batch_item2"]["value"] == ["batch", "list", "items"]
    
    def test_delete_knowledge(self, api, test_user):
        """Test deleting knowledge."""
        # Store knowledge
        api.store_knowledge(
            user_id=test_user.user_id,
            category_name="delete_test",
            value="Delete Me"
        )
        
        # Verify it exists
        knowledge = api.get_user_knowledge(test_user.user_id)
        assert "delete_test" in knowledge
        
        # Delete it
        api.delete_knowledge(test_user.user_id, "delete_test")
        
        # Verify it's gone
        knowledge = api.get_user_knowledge(test_user.user_id)
        assert "delete_test" not in knowledge
    
    def test_timestamp_filtering(self, api, test_user):
        """Test filtering knowledge by timestamp."""
        # Store old knowledge
        api.store_knowledge(
            user_id=test_user.user_id,
            category_name="old_timestamp",
            value="Old Value"
        )
        
        # Record timestamp
        time.sleep(1)  # Ensure different timestamps
        timestamp = int(time.time())
        time.sleep(1)  # Ensure different timestamps
        
        # Store new knowledge
        api.store_knowledge(
            user_id=test_user.user_id,
            category_name="new_timestamp",
            value="New Value"
        )
        
        # Get knowledge since timestamp
        recent_knowledge = api.get_user_knowledge(
            user_id=test_user.user_id,
            since_timestamp=timestamp
        )
        
        # Should only contain the new knowledge
        assert "new_timestamp" in recent_knowledge
        assert "old_timestamp" not in recent_knowledge
    
    def test_filtering_by_source(self, api, test_user):
        """Test filtering knowledge by source."""
        # Store knowledge with different sources
        api.store_knowledge(
            user_id=test_user.user_id,
            category_name="user_stated_item",
            value="User Stated",
            source="user_stated"
        )
        
        api.store_knowledge(
            user_id=test_user.user_id,
            category_name="extracted_item",
            value="Extracted",
            source="extracted"
        )
        
        # Get knowledge by source
        extracted_knowledge = api.get_knowledge_by_source(test_user.user_id, "extracted")
        
        # Should only contain extracted knowledge
        assert "extracted_item" in extracted_knowledge
        assert "user_stated_item" not in extracted_knowledge
    
    def test_merge_knowledge(self, api, test_user):
        """Test merging knowledge from one user to another."""
        # Create second user
        user2 = api.create_user(
            name="Merge Source",
            platform_name="terminal",
            platform_username="mergesource"
        )
        
        # Store knowledge for both users
        api.store_knowledge(
            user_id=test_user.user_id,
            category_name="shared_category",
            value="Target Value",
            confidence=0.5
        )
        
        api.store_knowledge(
            user_id=user2.user_id,
            category_name="shared_category",
            value="Source Value",
            confidence=0.8  # Higher confidence
        )
        
        api.store_knowledge(
            user_id=user2.user_id,
            category_name="unique_category",
            value="Unique Value",
            confidence=0.7
        )
        
        # Merge knowledge from user2 to test_user
        api.merge_knowledge(test_user.user_id, user2.user_id)
        
        # Get knowledge for test_user
        knowledge = api.get_user_knowledge(test_user.user_id)
        
        # Should have merged the higher confidence shared value
        assert knowledge["shared_category"]["value"] == "Source Value"
        assert knowledge["shared_category"]["confidence"] == 0.8
        
        # Should have added the unique category
        assert "unique_category" in knowledge
        assert knowledge["unique_category"]["value"] == "Unique Value"