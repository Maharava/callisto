"""Core API for interacting with the Callisto memory database."""
from datetime import datetime
import json
from typing import Dict, List, Optional, Any

from .db import db
from .models import (
    User, Platform, UserPlatform, 
    KnowledgeCategory, UserKnowledge,
    Conversation, Message, ExtractionJob
)
from .interfaces import CallistoAPIInterface
from .validation import (
    UserCreateModel, KnowledgeStoreModel, 
    CategoryCreateModel, MessageAddModel
)
from .security import sanitize_input, validate_uuid, secure_delete

class CallistoAPI(CallistoAPIInterface):
    """Main API for Jupiter to interact with Callisto memory system."""
    
    def get_user(self, platform_name: str, platform_username: str) -> Optional[User]:
        """Find a user by platform and username."""
        # Sanitize inputs
        platform_name = sanitize_input(platform_name)
        platform_username = sanitize_input(platform_username)
        
        with db.session() as session:
            # Find platform
            platform = session.query(Platform).filter_by(platform_name=platform_name).first()
            if not platform:
                return None
                
            # Find user via platform
            user_platform = (session.query(UserPlatform)
                .filter_by(platform_id=platform.platform_id, platform_username=platform_username)
                .first())
            
            if not user_platform:
                return None
                
            return session.query(User).filter_by(user_id=user_platform.user_id).first()
    
    def create_user(self, name: str, platform_name: str, platform_username: str, 
                   platform_specific_id: Optional[str] = None) -> User:
        """Create a new user with platform association."""
        # Validate inputs
        UserCreateModel(
            name=name,
            platform_name=platform_name,
            platform_username=platform_username,
            platform_specific_id=platform_specific_id
        )
        
        # Sanitize inputs
        name = sanitize_input(name)
        platform_name = sanitize_input(platform_name)
        platform_username = sanitize_input(platform_username)
        platform_specific_id = sanitize_input(platform_specific_id) if platform_specific_id else None
        
        with db.session() as session:
            # Find or create platform
            platform = session.query(Platform).filter_by(platform_name=platform_name).first()
            if not platform:
                platform = Platform(platform_name=platform_name)
                session.add(platform)
                session.flush()
            
            # Create user
            user = User.create(name=name)
            session.add(user)
            session.flush()
            
            # Create platform association
            now = int(datetime.now().timestamp())
            user_platform = UserPlatform(
                user_id=user.user_id,
                platform_id=platform.platform_id,
                platform_username=platform_username,
                platform_specific_id=platform_specific_id,
                last_active=now
            )
            session.add(user_platform)
            
            return user
    
    def update_user(self, user_id: str, name: str) -> None:
        """Update user information."""
        if not validate_uuid(user_id):
            raise ValueError("Invalid user ID format")
            
        name = sanitize_input(name)
        
        with db.session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.name = name
    
    def delete_user(self, user_id: str) -> None:
        """Delete a user and all associated data."""
        if not validate_uuid(user_id):
            raise ValueError("Invalid user ID format")
            
        with db.session() as session:
            # Securely delete personal knowledge
            knowledge_items = (session.query(UserKnowledge)
                .join(KnowledgeCategory)
                .filter(UserKnowledge.user_id == user_id, KnowledgeCategory.is_personal == True)
                .all())
                
            for item in knowledge_items:
                item.value = secure_delete(item.value)
                session.add(item)
            
            # Delete the user
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                session.delete(user)
    
    def link_platform(self, user_id: str, platform_name: str, platform_username: str,
                    platform_specific_id: Optional[str] = None) -> None:
        """Link a user to a platform."""
        if not validate_uuid(user_id):
            raise ValueError("Invalid user ID format")
            
        platform_name = sanitize_input(platform_name)
        platform_username = sanitize_input(platform_username)
        platform_specific_id = sanitize_input(platform_specific_id) if platform_specific_id else None
        
        with db.session() as session:
            # Find or create platform
            platform = session.query(Platform).filter_by(platform_name=platform_name).first()
            if not platform:
                platform = Platform(platform_name=platform_name)
                session.add(platform)
                session.flush()
            
            # Check if user exists
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Check if platform link already exists
            existing = (session.query(UserPlatform)
                .filter_by(
                    user_id=user_id,
                    platform_id=platform.platform_id,
                    platform_username=platform_username
                )
                .first())
                
            if not existing:
                # Create platform association
                now = int(datetime.now().timestamp())
                user_platform = UserPlatform(
                    user_id=user_id,
                    platform_id=platform.platform_id,
                    platform_username=platform_username,
                    platform_specific_id=platform_specific_id,
                    last_active=now
                )
                session.add(user_platform)
    
    def get_user_knowledge(self, user_id: str) -> Dict[str, Any]:
        """Get all knowledge for a user, categorised."""
        if not validate_uuid(user_id):
            raise ValueError("Invalid user ID format")
            
        with db.session() as session:
            knowledge_items = (session.query(UserKnowledge, KnowledgeCategory)
                .join(KnowledgeCategory)
                .filter(UserKnowledge.user_id == user_id)
                .all())
            
            result = {}
            for knowledge, category in knowledge_items:
                # Convert value based on data type
                if category.data_type == "list":
                    try:
                        value = json.loads(knowledge.value)
                    except:
                        value = knowledge.value
                elif category.data_type == "number":
                    try:
                        value = float(knowledge.value)
                    except:
                        value = knowledge.value
                elif category.data_type == "boolean":
                    value = knowledge.value.lower() in ('true', 'yes', '1')
                else:
                    value = knowledge.value
                    
                if category.category_name not in result:
                    result[category.category_name] = {
                        "value": value,
                        "confidence": knowledge.confidence,
                        "source": knowledge.source,
                        "is_personal": category.is_personal
                    }
                elif knowledge.confidence > result[category.category_name]["confidence"]:
                    # Keep the highest confidence value
                    result[category.category_name] = {
                        "value": value,
                        "confidence": knowledge.confidence,
                        "source": knowledge.source,
                        "is_personal": category.is_personal
                    }
            
            return result
    
    def store_knowledge(self, user_id: str, category_name: str, value: Any, 
                       confidence: float = 1.0, source: str = "user_stated") -> None:
        """Store a piece of knowledge about a user."""
        # Validate inputs
        KnowledgeStoreModel(
            user_id=user_id,
            category_name=category_name,
            value=value,
            confidence=confidence,
            source=source
        )
        
        # Sanitize inputs
        category_name = sanitize_input(category_name)
        
        # Sanitize value if it's a string or list
        if isinstance(value, str):
            value = sanitize_input(value)
        elif isinstance(value, list):
            value = [sanitize_input(item) if isinstance(item, str) else item for item in value]
            
        with db.session() as session:
            # Find category
            category = session.query(KnowledgeCategory).filter_by(category_name=category_name).first()
            if not category:
                # Determine data type
                if isinstance(value, list):
                    data_type = "list"
                elif isinstance(value, bool):
                    data_type = "boolean"
                elif isinstance(value, (int, float)):
                    data_type = "number"
                else:
                    data_type = "string"
                    
                # Create new category if it doesn't exist
                category = KnowledgeCategory(
                    category_name=category_name,
                    data_type=data_type,
                    is_personal=False
                )
                session.add(category)
                session.flush()
            
            # Convert value to string
            if category.data_type == "list" and not isinstance(value, str):
                value_str = json.dumps(value)
            else:
                value_str = str(value)
            
            now = int(datetime.now().timestamp())
            
            # Create or update knowledge
            knowledge = (session.query(UserKnowledge)
                .filter_by(user_id=user_id, category_id=category.category_id)
                .first())
                
            if knowledge:
                knowledge.value = value_str
                knowledge.confidence = confidence
                knowledge.source = source
                knowledge.updated_at = now
            else:
                knowledge = UserKnowledge(
                    user_id=user_id,
                    category_id=category.category_id,
                    value=value_str,
                    confidence=confidence,
                    source=source,
                    created_at=now,
                    updated_at=now
                )
                session.add(knowledge)
    
    def delete_knowledge(self, user_id: str, category_name: str) -> None:
        """Delete a piece of knowledge about a user."""
        if not validate_uuid(user_id):
            raise ValueError("Invalid user ID format")
            
        category_name = sanitize_input(category_name)
        
        with db.session() as session:
            # Find category
            category = session.query(KnowledgeCategory).filter_by(category_name=category_name).first()
            if not category:
                return
            
            # Find and delete knowledge
            knowledge = (session.query(UserKnowledge)
                .filter_by(user_id=user_id, category_id=category.category_id)
                .first())
                
            if knowledge:
                # Securely delete if personal
                if category.is_personal:
                    knowledge.value = secure_delete(knowledge.value)
                    session.add(knowledge)
                
                session.delete(knowledge)
    
    def get_knowledge_categories(self) -> List[Dict[str, Any]]:
        """Get all knowledge categories."""
        with db.session() as session:
            categories = session.query(KnowledgeCategory).all()
            return [
                {
                    "category_name": cat.category_name,
                    "data_type": cat.data_type,
                    "is_personal": cat.is_personal
                }
                for cat in categories
            ]
    
    def create_knowledge_category(self, category_name: str, data_type: str, 
                                is_personal: bool = False) -> None:
        """Create a new knowledge category."""
        # Validate inputs
        CategoryCreateModel(
            category_name=category_name,
            data_type=data_type,
            is_personal=is_personal
        )
        
        # Sanitize inputs
        category_name = sanitize_input(category_name)
        
        with db.session() as session:
            # Check if category already exists
            existing = session.query(KnowledgeCategory).filter_by(category_name=category_name).first()
            if not existing:
                category = KnowledgeCategory(
                    category_name=category_name,
                    data_type=data_type,
                    is_personal=is_personal
                )
                session.add(category)
    
    def start_conversation(self, user_id: str, platform_name: str) -> str:
        """Start a new conversation and return the conversation ID."""
        if not validate_uuid(user_id):
            raise ValueError("Invalid user ID format")
            
        platform_name = sanitize_input(platform_name)
        
        with db.session() as session:
            # Find platform
            platform = session.query(Platform).filter_by(platform_name=platform_name).first()
            if not platform:
                platform = Platform(platform_name=platform_name)
                session.add(platform)
                session.flush()
            
            # Create conversation
            conversation = Conversation.create(user_id, platform.platform_id)
            session.add(conversation)
            
            # Update user last seen
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.last_seen = conversation.started_at
            
            return conversation.conversation_id
    
    def add_message(self, conversation_id: str, content: str, is_from_user: bool) -> None:
        """Add a message to a conversation."""
        # Validate inputs
        MessageAddModel(
            conversation_id=conversation_id,
            content=content,
            is_from_user=is_from_user
        )
        
        content = sanitize_input(content)
        
        with db.session() as session:
            now = int(datetime.now().timestamp())
            message = Message(
                conversation_id=conversation_id,
                is_from_user=is_from_user,
                content=content,
                timestamp=now
            )
            session.add(message)
            
            # Update user last seen
            conversation = session.query(Conversation).filter_by(conversation_id=conversation_id).first()
            if conversation:
                user = session.query(User).filter_by(user_id=conversation.user_id).first()
                if user:
                    user.last_seen = now
    
    def end_conversation(self, conversation_id: str) -> None:
        """End a conversation."""
        if not validate_uuid(conversation_id):
            raise ValueError("Invalid conversation ID format")
            
        with db.session() as session:
            conversation = session.query(Conversation).filter_by(conversation_id=conversation_id).first()
            if conversation and not conversation.ended_at:
                conversation.ended_at = int(datetime.now().timestamp())
                
                # Create extraction job
                job = ExtractionJob(
                    conversation_id=conversation_id,
                    status="pending",
                    created_at=conversation.ended_at
                )
                session.add(job)
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a conversation."""
        if not validate_uuid(conversation_id):
            raise ValueError("Invalid conversation ID format")
            
        with db.session() as session:
            messages = (session.query(Message)
                .filter_by(conversation_id=conversation_id)
                .order_by(Message.timestamp)
                .all())
                
            return [
                {
                    "message_id": message.message_id,
                    "is_from_user": message.is_from_user,
                    "content": message.content,
                    "timestamp": message.timestamp
                }
                for message in messages
            ]

# Create global API instance for easy import
api = CallistoAPI()