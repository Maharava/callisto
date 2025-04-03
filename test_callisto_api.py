"""
Comprehensive test script for Callisto API.
Calls all major API functions with test data.
"""
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("callisto_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("callisto_test")

# Import callisto modules
try:
    import callisto
    from callisto.api import api
    logger.info("Successfully imported Callisto modules")
except ImportError as e:
    logger.error(f"Failed to import Callisto: {e}")
    sys.exit(1)

def load_test_data():
    """Load test data from files."""
    logger.info("Loading test data files")
    
    # Load user data
    try:
        with open("fakeuser.json", "r") as f:
            user_data = json.load(f)
            logger.info(f"Loaded user data: {len(user_data)} users")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load user data: {e}")
        user_data = {
            "name": "Test User",
            "platform_name": "test_platform",
            "platform_username": "testuser123",
            "knowledge": [
                {"category": "favorite_color", "value": "blue", "confidence": 0.9},
                {"category": "hobbies", "value": ["reading", "hiking"], "confidence": 0.8},
                {"category": "location", "value": "New York", "confidence": 0.95}
            ]
        }
        logger.info("Using fallback user data")
    
    # Load conversation data
    try:
        with open("fakconvo.txt", "r") as f:
            convo_text = f.read()
            logger.info(f"Loaded conversation data: {len(convo_text)} characters")
    except FileNotFoundError as e:
        logger.error(f"Failed to load conversation data: {e}")
        convo_text = """
User: Hello, how are you today?
AI: I'm doing well, thank you for asking! How are you?
User: I'm good. I've been thinking about learning Python.
AI: That's great! Python is a versatile language with many applications.
User: Do you have any resources you'd recommend?
AI: Absolutely! For beginners, I'd recommend Python.org tutorials, Codecademy, and the book "Automate the Boring Stuff".
"""
        logger.info("Using fallback conversation data")
    
    # Parse conversation into messages
    messages = parse_conversation(convo_text)
    logger.info(f"Parsed {len(messages)} messages from conversation")
    
    return user_data, messages

def parse_conversation(convo_text: str) -> List[Dict[str, Any]]:
    """Parse conversation text into structured messages."""
    lines = convo_text.strip().split('\n')
    messages = []
    timestamp = int(time.time())
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("User:"):
            messages.append({
                "content": line[5:].strip(),
                "is_from_user": True,
                "timestamp": timestamp
            })
        elif line.startswith("AI:"):
            messages.append({
                "content": line[3:].strip(),
                "is_from_user": False,
                "timestamp": timestamp
            })
        
        timestamp += 10  # Space messages 10 seconds apart
    
    return messages

def test_user_management(user_data):
    """Test user management functionality."""
    logger.info("=== TESTING USER MANAGEMENT ===")
    
    # Create user
    try:
        logger.info(f"Creating user: {user_data['name']}")
        user = api.create_user(
            name=user_data["name"],
            platform_name=user_data["platform_name"],
            platform_username=user_data["platform_username"]
        )
        logger.info(f"User created with ID: {user.user_id}")
        user_id = user.user_id
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        # Create a temporary UUID for testing other functions
        user_id = str(uuid.uuid4())
        logger.info(f"Using temporary user ID: {user_id}")
    
    # Get user
    try:
        logger.info(f"Retrieving user by platform: {user_data['platform_name']}/{user_data['platform_username']}")
        retrieved_user = api.get_user(
            platform_name=user_data["platform_name"],
            platform_username=user_data["platform_username"]
        )
        if retrieved_user:
            logger.info(f"Retrieved user: {retrieved_user.name} (ID: {retrieved_user.user_id})")
        else:
            logger.warning("User not found")
    except Exception as e:
        logger.error(f"Failed to retrieve user: {e}")
    
    # Update user
    try:
        new_name = f"{user_data['name']} (Updated)"
        logger.info(f"Updating user {user_id} name to: {new_name}")
        api.update_user(user_id=user_id, name=new_name)
        logger.info("User updated successfully")
    except Exception as e:
        logger.error(f"Failed to update user: {e}")
    
    # Link platform
    try:
        new_platform = "discord"
        new_username = f"{user_data['platform_username']}_discord"
        logger.info(f"Linking user {user_id} to platform: {new_platform}/{new_username}")
        api.link_platform(
            user_id=user_id,
            platform_name=new_platform,
            platform_username=new_username
        )
        logger.info("Platform linked successfully")
    except Exception as e:
        logger.error(f"Failed to link platform: {e}")
    
    return user_id

def test_category_management():
    """Test category management functionality."""
    logger.info("=== TESTING CATEGORY MANAGEMENT ===")
    
    # Get categories
    try:
        logger.info("Retrieving all knowledge categories")
        categories = api.get_knowledge_categories()
        logger.info(f"Retrieved {len(categories)} categories")
        for i, cat in enumerate(categories[:5]):  # Show first 5 only
            logger.info(f"  Category {i+1}: {cat['category_name']} ({cat['data_type']})")
        if len(categories) > 5:
            logger.info(f"  ... and {len(categories) - 5} more")
    except Exception as e:
        logger.error(f"Failed to retrieve categories: {e}")
    
    # Create category
    test_categories = [
        {"name": "test_string_category", "type": "string"},
        {"name": "test_list_category", "type": "list"},
        {"name": "test_number_category", "type": "number"},
        {"name": "test_personal_category", "type": "string", "personal": True}
    ]
    
    for cat in test_categories:
        try:
            logger.info(f"Creating category: {cat['name']} ({cat['type']})")
            is_personal = cat.get("personal", False)
            result = api.create_knowledge_category(
                category_name=cat["name"],
                data_type=cat["type"],
                is_personal=is_personal
            )
            logger.info(f"Category created: {result}")
        except Exception as e:
            logger.error(f"Failed to create category: {e}")
    
    # Update category
    try:
        logger.info("Updating test_string_category to be personal")
        result = api.update_knowledge_category(
            category_name="test_string_category",
            is_personal=True
        )
        logger.info(f"Category updated: {result}")
    except Exception as e:
        logger.error(f"Failed to update category: {e}")
    
    # Get non-personal categories
    try:
        logger.info("Retrieving non-personal categories")
        non_personal = api.get_knowledge_categories(include_personal=False)
        logger.info(f"Retrieved {len(non_personal)} non-personal categories")
    except Exception as e:
        logger.error(f"Failed to retrieve non-personal categories: {e}")
    
    # Delete a category
    try:
        category_to_delete = "test_string_category"
        logger.info(f"Deleting category: {category_to_delete}")
        result = api.delete_knowledge_category(category_to_delete)
        logger.info(f"Category deleted: {result}")
    except Exception as e:
        logger.error(f"Failed to delete category: {e}")

def test_knowledge_management(user_id, user_data):
    """Test knowledge management functionality."""
    logger.info("=== TESTING KNOWLEDGE MANAGEMENT ===")
    
    # Store knowledge
    for item in user_data.get("knowledge", []):
        try:
            logger.info(f"Storing knowledge: {item['category']} = {item['value']}")
            api.store_knowledge(
                user_id=user_id,
                category_name=item["category"],
                value=item["value"],
                confidence=item.get("confidence", 1.0),
                source=item.get("source", "user_stated")
            )
            logger.info("Knowledge stored successfully")
        except Exception as e:
            logger.error(f"Failed to store knowledge: {e}")
    
    # Get user knowledge
    try:
        logger.info(f"Retrieving all knowledge for user {user_id}")
        knowledge = api.get_user_knowledge(user_id)
        logger.info(f"Retrieved {len(knowledge)} knowledge items")
        for category, data in knowledge.items():
            logger.info(f"  {category}: {data['value']} (confidence: {data['confidence']})")
    except Exception as e:
        logger.error(f"Failed to retrieve knowledge: {e}")
    
    # Batch store knowledge
    try:
        logger.info("Batch storing extracted knowledge")
        extracted_items = [
            {"category": "favorite_food", "value": "pizza", "confidence": 0.7, "source": "extracted"},
            {"category": "favorite_movie", "value": "The Matrix", "confidence": 0.6, "source": "extracted"}
        ]
        api.batch_store_knowledge(user_id, extracted_items)
        logger.info("Batch knowledge stored successfully")
    except Exception as e:
        logger.error(f"Failed to batch store knowledge: {e}")
    
    # Get knowledge by source
    try:
        logger.info("Retrieving knowledge by source='extracted'")
        extracted = api.get_knowledge_by_source(user_id, "extracted")
        logger.info(f"Retrieved {len(extracted)} extracted knowledge items")
        for category, data in extracted.items():
            logger.info(f"  {category}: {data['value']}")
    except Exception as e:
        logger.error(f"Failed to retrieve extracted knowledge: {e}")
    
    # Delete knowledge
    try:
        category_to_delete = "favorite_food"
        logger.info(f"Deleting knowledge: {category_to_delete}")
        api.delete_knowledge(user_id, category_to_delete)
        logger.info("Knowledge deleted successfully")
    except Exception as e:
        logger.error(f"Failed to delete knowledge: {e}")

def test_conversation_management(user_id, messages):
    """Test conversation management functionality."""
    logger.info("=== TESTING CONVERSATION MANAGEMENT ===")
    
    # Start conversation
    try:
        logger.info(f"Starting new conversation for user {user_id}")
        conversation_id = api.start_conversation(
            user_id=user_id,
            platform_name="test_platform"
        )
        logger.info(f"Conversation started with ID: {conversation_id}")
    except Exception as e:
        logger.error(f"Failed to start conversation: {e}")
        # Create a temporary conversation ID for testing other functions
        conversation_id = str(uuid.uuid4())
        logger.info(f"Using temporary conversation ID: {conversation_id}")
    
    # Add messages
    try:
        logger.info(f"Adding {len(messages)} messages to conversation {conversation_id}")
        for i, msg in enumerate(messages):
            logger.info(f"  Adding message {i+1}: {msg['content'][:30]}...")
            api.add_message(
                conversation_id=conversation_id,
                content=msg["content"],
                is_from_user=msg["is_from_user"]
            )
        logger.info("All messages added successfully")
    except Exception as e:
        logger.error(f"Failed to add messages: {e}")
    
    # Get conversation history
    try:
        logger.info(f"Retrieving conversation history for {conversation_id}")
        history = api.get_conversation_history(conversation_id)
        logger.info(f"Retrieved {len(history)} messages")
        for i, msg in enumerate(history):
            sender = "User" if msg["is_from_user"] else "AI"
            logger.info(f"  Message {i+1} [{sender}]: {msg['content'][:30]}...")
    except Exception as e:
        logger.error(f"Failed to retrieve conversation history: {e}")
    
    # Store a complete conversation at once
    try:
        logger.info("Storing a complete conversation at once")
        new_conversation_id = api.store_conversation(
            user_id=user_id,
            platform_name="test_platform",
            messages=messages
        )
        logger.info(f"Stored conversation with ID: {new_conversation_id}")
    except Exception as e:
        logger.error(f"Failed to store conversation: {e}")
        new_conversation_id = conversation_id
    
    # Get recent conversations
    try:
        logger.info(f"Retrieving recent conversations for user {user_id}")
        recent = api.get_recent_conversations(user_id, limit=5)
        logger.info(f"Retrieved {len(recent)} recent conversations")
        for i, conv in enumerate(recent):
            logger.info(f"  Conversation {i+1}: {conv['conversation_id']} (processed: {conv['processed']})")
    except Exception as e:
        logger.error(f"Failed to retrieve recent conversations: {e}")
    
    # Mark conversation as processed
    try:
        logger.info(f"Marking conversation {new_conversation_id} as processed")
        api.mark_conversation_processed(new_conversation_id)
        logger.info("Conversation marked as processed")
    except Exception as e:
        logger.error(f"Failed to mark conversation as processed: {e}")
    
    # End conversation
    try:
        logger.info(f"Ending conversation {conversation_id}")
        api.end_conversation(conversation_id)
        logger.info("Conversation ended successfully")
    except Exception as e:
        logger.error(f"Failed to end conversation: {e}")
    
    # Store multiple conversations in batch
    try:
        logger.info("Batch storing conversations")
        batch_conversations = [
            {"messages": messages[:2]},
            {"messages": messages[2:4]}
        ]
        batch_ids = api.batch_store_conversations(
            user_id=user_id,
            platform_name="test_platform",
            conversations=batch_conversations
        )
        logger.info(f"Batch stored {len(batch_ids)} conversations")
    except Exception as e:
        logger.error(f"Failed to batch store conversations: {e}")

def test_cleanup(user_id):
    """Clean up test data."""
    logger.info("=== CLEANUP ===")
    
    # Delete user
    try:
        logger.info(f"Deleting test user {user_id}")
        api.delete_user(user_id)
        logger.info("User deleted successfully")
    except Exception as e:
        logger.error(f"Failed to delete user: {e}")

def main():
    """Main test function."""
    logger.info("Starting Callisto API Test")
    logger.info("===========================")
    
    # Initialize database
    try:
        db_path = os.path.join(os.getcwd(), "callisto_test.db")
        logger.info(f"Initializing database at: {db_path}")
        callisto.initialize(db_path)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)
    
    # Load test data
    user_data, messages = load_test_data()
    
    # Run tests
    try:
        # Test user management
        user_id = test_user_management(user_data)
        
        # Test category management
        test_category_management()
        
        # Test knowledge management
        test_knowledge_management(user_id, user_data)
        
        # Test conversation management
        test_conversation_management(user_id, messages)
        
        # Clean up test data
        test_cleanup(user_id)
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
    
    logger.info("===========================")
    logger.info("Callisto API Test Completed")

if __name__ == "__main__":
    main()