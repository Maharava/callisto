"""Integration tests for the Callisto API."""
import pytest
import tempfile
import os
import time
import uuid

import callisto
from callisto.api import api as global_api

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

class TestAPIIntegration:
    """Integration tests for the complete Callisto API workflow."""
    
    def test_full_workflow(self, api):
        """Test a complete workflow from user creation to knowledge retrieval."""
        # 1. Create user
        user = api.create_user(
            name="Integration Test",
            platform_name="discord",
            platform_username="integrationtest"
        )
        
        # 2. Create custom knowledge categories
        api.create_knowledge_category(
            category_name="favorite_color",
            data_type="string",
            is_personal=False
        )
        
        api.create_knowledge_category(
            category_name="hobbies",
            data_type="list",
            is_personal=False
        )
        
        # 3. Store conversation
        messages = [
            {"content": "I like the color blue", "is_from_user": True, "timestamp": int(time.time())},
            {"content": "Blue is a great color!", "is_from_user": False, "timestamp": int(time.time())},
            {"content": "I enjoy hiking and reading", "is_from_user": True, "timestamp": int(time.time())},
            {"content": "Those are wonderful hobbies!", "is_from_user": False, "timestamp": int(time.time())}
        ]
        
        conversation_id = api.store_conversation(
            user_id=user.user_id,
            platform_name="discord",
            messages=messages
        )
        
        # 4. Get conversation history
        history = api.get_conversation_history(conversation_id)
        assert len(history) == 4
        
        # 5. Store knowledge (as if extracted by Jupiter)
        extracted_knowledge = [
            {
                "category": "favorite_color",
                "value": "blue",
                "confidence": 0.8,
                "source": "extracted"
            },
            {
                "category": "hobbies",
                "value": ["hiking", "reading"],
                "confidence": 0.7,
                "source": "extracted"
            }
        ]
        
        api.batch_store_knowledge(user.user_id, extracted_knowledge)
        
        # 6. Mark conversation as processed
        api.mark_conversation_processed(conversation_id)
        
        # 7. Get user knowledge
        knowledge = api.get_user_knowledge(user.user_id)
        
        assert "favorite_color" in knowledge
        assert knowledge["favorite_color"]["value"] == "blue"
        
        assert "hobbies" in knowledge
        assert "hiking" in knowledge["hobbies"]["value"]
        assert "reading" in knowledge["hobbies"]["value"]
        
        # 8. Get knowledge by source
        extracted = api.get_knowledge_by_source(user.user_id, "extracted")
        assert "favorite_color" in extracted
        assert "hobbies" in extracted
        
        # 9. Get recent conversations (should be empty since we marked it processed)
        unprocessed = api.get_recent_conversations(
            user_id=user.user_id,
            include_processed=False
        )
        
        assert len(unprocessed) == 0
    
    def test_global_api_instance(self):
        """Test that the global API instance works."""
        # Just verify it can be accessed
        assert global_api is not None
        
        # Should be able to get categories
        categories = global_api.get_knowledge_categories()
        assert isinstance(categories, list)
        assert len(categories) > 0
    
    def test_input_sanitization(self, api):
        """Test that inputs are properly sanitized."""
        # Create user with potentially dangerous name
        user = api.create_user(
            name="<script>alert('XSS')</script>",
            platform_name="terminal",
            platform_username="xsstest"
        )
        
        # Retrieve user
        retrieved = api.get_user("terminal", "xsstest")
        
        # Name should be sanitized
        assert "<script>" not in retrieved.name
        
        # Store knowledge with potentially dangerous content
        api.store_knowledge(
            user_id=user.user_id,
            category_name="dangerous",
            value="<img src=x onerror=alert('XSS')>"
        )
        
        # Retrieve knowledge
        knowledge = api.get_user_knowledge(user.user_id)
        
        # Value should be sanitized
        assert "<img" not in knowledge["dangerous"]["value"]