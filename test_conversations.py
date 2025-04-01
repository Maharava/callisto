"""Tests for conversation storage and retrieval functionality."""
import pytest
import tempfile
import os
import time
import uuid

import callisto
from callisto.models import Conversation, Message

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
        name="Conversation Test",
        platform_name="terminal",
        platform_username="convtest"
    )
    return user

class TestConversationManagement:
    """Test conversation management functionality."""
    
    def test_store_and_retrieve_conversation(self, api, test_user):
        """Test storing and retrieving a conversation."""
        # Sample messages
        messages = [
            {"content": "Hello", "is_from_user": True, "timestamp": int(time.time())},
            {"content": "Hi there!", "is_from_user": False, "timestamp": int(time.time())}
        ]
        
        # Store conversation
        conversation_id = api.store_conversation(
            user_id=test_user.user_id,
            platform_name="terminal",
            messages=messages
        )
        
        assert conversation_id is not None
        
        # Retrieve conversation history
        history = api.get_conversation_history(conversation_id)
        
        assert len(history) == 2
        assert history[0]["content"] == "Hello"
        assert history[0]["is_from_user"] == True
        assert history[1]["content"] == "Hi there!"
        assert history[1]["is_from_user"] == False
    
    def test_store_with_custom_id(self, api, test_user):
        """Test storing a conversation with a custom ID."""
        custom_id = str(uuid.uuid4())
        messages = [{"content": "Test", "is_from_user": True}]
        
        conversation_id = api.store_conversation(
            user_id=test_user.user_id,
            platform_name="terminal",
            messages=messages,
            conversation_id=custom_id
        )
        
        assert conversation_id == custom_id
        
        # Verify it can be retrieved
        history = api.get_conversation_history(custom_id)
        assert len(history) == 1
    
    def test_batch_store_conversations(self, api, test_user):
        """Test batch storing of conversations."""
        conversations = [
            {
                "messages": [
                    {"content": "Batch 1 Message 1", "is_from_user": True},
                    {"content": "Batch 1 Response", "is_from_user": False}
                ]
            },
            {
                "messages": [
                    {"content": "Batch 2 Message 1", "is_from_user": True},
                    {"content": "Batch 2 Response", "is_from_user": False}
                ]
            }
        ]
        
        conversation_ids = api.batch_store_conversations(
            user_id=test_user.user_id,
            platform_name="terminal",
            conversations=conversations
        )
        
        assert len(conversation_ids) == 2
        
        # Verify conversations were stored
        for conv_id in conversation_ids:
            history = api.get_conversation_history(conv_id)
            assert len(history) == 2
    
    def test_mark_conversation_processed(self, api, test_user):
        """Test marking a conversation as processed."""
        # Store conversation
        messages = [{"content": "Process me", "is_from_user": True}]
        conversation_id = api.store_conversation(
            user_id=test_user.user_id,
            platform_name="terminal",
            messages=messages
        )
        
        # Get recent conversations (should include unprocessed)
        recent = api.get_recent_conversations(
            user_id=test_user.user_id,
            include_processed=False
        )
        
        assert len(recent) >= 1
        assert conversation_id in [conv["conversation_id"] for conv in recent]
        
        # Mark as processed
        api.mark_conversation_processed(conversation_id)
        
        # Get unprocessed conversations (should not include marked one)
        unprocessed = api.get_recent_conversations(
            user_id=test_user.user_id,
            include_processed=False
        )
        
        assert conversation_id not in [conv["conversation_id"] for conv in unprocessed]
    
    def test_get_recent_conversations(self, api, test_user):
        """Test getting recent conversations."""
        # Store several conversations with different timestamps
        old_time = int(time.time()) - 3600  # 1 hour ago
        
        # Old conversation
        old_messages = [{"content": "Old", "is_from_user": True, "timestamp": old_time}]
        old_conv_id = api.store_conversation(
            user_id=test_user.user_id,
            platform_name="terminal",
            messages=old_messages
        )
        
        time.sleep(1)  # Ensure different timestamps
        
        # Recent conversation
        new_messages = [{"content": "New", "is_from_user": True}]
        new_conv_id = api.store_conversation(
            user_id=test_user.user_id,
            platform_name="terminal",
            messages=new_messages
        )
        
        # Get all recent conversations
        all_recent = api.get_recent_conversations(test_user.user_id)
        assert len(all_recent) >= 2
        
        # Should be ordered by most recent first
        assert all_recent[0]["conversation_id"] == new_conv_id
        
        # Test filtering by timestamp
        filtered = api.get_recent_conversations(
            user_id=test_user.user_id,
            since_timestamp=old_time + 1  # Just after old conversation
        )
        
        filtered_ids = [conv["conversation_id"] for conv in filtered]
        assert new_conv_id in filtered_ids
        assert old_conv_id not in filtered_ids