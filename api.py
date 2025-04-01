"""Core API for interacting with the Callisto memory database."""
from datetime import datetime
import json
from typing import Dict, List, Optional, Any, Union

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
from .knowledge import KnowledgeManager
from .categories import CategoryManager
from .conversations import ConversationManager

class CallistoAPI(CallistoAPIInterface):
    """Main API for Jupiter to interact with Callisto memory system."""
    
    # USER MANAGEMENT
    
    def get_user(self, platform_name: str, platform_username: str) -> Optional[User]:
        """Find a user by platform and username."""
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
    
    # KNOWLEDGE MANAGEMENT
    
    def get_user_knowledge(self, user_id: str, category_name: Optional[str] = None, 
                          include_personal: bool = True) -> Dict[str, Any]:
        """Get all knowledge for a user, with optional filtering."""
        if not validate_uuid(user_id):
            raise ValueError("Invalid user ID format")
        
        if category_name:
            category_name = sanitize_input(category_name)
            
        # Use knowledge manager for retrieval
        is_personal = None if include_personal else False
        return KnowledgeManager.get_knowledge(user_id, category_name, is_personal)
    
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
        
        if not validate_uuid(user_id):
            raise ValueError("Invalid user ID format")
            
        # Use knowledge manager for storage
        KnowledgeManager.store_knowledge(user_id, category_name, value, confidence, source)
    
    def batch_store_knowledge(self, user_id: str, knowledge_items: List[Dict[str, Any]]) -> None:
        """Store multiple knowledge items at once."""
        if not validate_uuid(user_id):
            raise ValueError("Invalid user ID format")
            
        # Use knowledge manager for batch storage
        KnowledgeManager.batch_store_knowledge(user_id, knowledge_items)
    
    def delete_knowledge(self, user_id: str, category_name: str) -> None:
        """Delete a piece of knowledge about a user."""
        if not validate_uuid(user_id):
            raise ValueError("Invalid user ID format")
            
        category_name = sanitize_input(category_name)
        KnowledgeManager.delete_knowledge(user_id, category_name)
    
    def merge_knowledge(self, user_id: str, target_user_id: str) -> None:
        """Merge knowledge from target user into this user."""
        if not validate_uuid(user_id) or not validate_uuid(target_user_id):
            raise ValueError("Invalid user ID format")
            
        KnowledgeManager.merge_knowledge(user_id, target_user_id)
    
    # CATEGORY MANAGEMENT
    
    def get_knowledge_categories(self, include_personal: bool = True) -> List[Dict[str, Any]]:
        """Get all knowledge categories."""
        return CategoryManager.get_categories(include_personal)
    
    def create_knowledge_category(self, category_name: str, data_type: str, 
                                is_personal: bool = False) -> bool:
        """Create a new knowledge category."""
        # Validate inputs
        CategoryCreateModel(
            category_name=category_name,
            data_type=data_type,
            is_personal=is_personal
        )
        
        return CategoryManager.create_category(category_name, data_type, is_personal)
    
    def update_knowledge_category(self, category_name: str, data_type: Optional[str] = None,
                                is_personal: Optional[bool] = None) -> bool:
        """Update an existing knowledge category."""
        category_name = sanitize_input(category_name)
        return CategoryManager.update_category(category_name, data_type, is_personal)
    
    def delete_knowledge_category(self, category_name: str) -> bool:
        """Delete a knowledge category."""
        category_name = sanitize_input(category_name)
        return CategoryManager.delete_category(category_name)
    
    # CONVERSATION MANAGEMENT
    
    def store_conversation(self, user_id: str, platform_name: str, messages: List[Dict[str, Any]], 
                         conversation_id: Optional[str] = None) -> str:
        """Store a complete conversation."""
        if not validate_uuid(user_id):
            raise ValueError("Invalid user ID format")
            
        platform_name = sanitize_input(platform_name)
        
        # Create conversation
        with db.session() as session:
            # Find platform
            platform = session.query(Platform).filter_by(platform_name=platform_name).first()
            if not platform:
                platform = Platform(platform_name=platform_name)
                session.add(platform)
                session.flush()
            
            # Create conversation with provided ID or generate one
            now = int(datetime.now().timestamp())
            if conversation_id and validate_uuid(conversation_id):
                # Check if conversation already exists
                existing = session.query(Conversation).filter_by(conversation_id=conversation_id).first()
                if existing:
                    return existing.conversation_id
                    
                conv = Conversation(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    platform_id=platform.platform_id,
                    started_at=now
                )
            else:
                conv = Conversation.create(user_id, platform.platform_id)
                
            session.add(conv)
            session.flush()
            
            # Add messages
            for msg in messages:
                content = sanitize_input(msg.get("content", ""))
                is_from_user = msg.get("is_from_user", True)
                timestamp = msg.get("timestamp", now)
                
                message = Message(
                    conversation_id=conv.conversation_id,
                    is_from_user=is_from_user,
                    content=content,
                    timestamp=timestamp
                )
                session.add(message)
            
            # Update user last seen
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.last_seen = now
                
            return conv.conversation_id
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a conversation."""
        if not validate_uuid(conversation_id):
            raise ValueError("Invalid conversation ID format")
            
        return ConversationManager.get_conversation_history(conversation_id)
    
    def get_recent_conversations(self, user_id: str, limit: int = 10, 
                               include_processed: bool = True) -> List[Dict[str, Any]]:
        """Get recent conversations for a user."""
        if not validate_uuid(user_id):
            raise ValueError("Invalid user ID format")
            
        with db.session() as session:
            query = session.query(Conversation).filter_by(user_id=user_id)
            
            if not include_processed:
                query = query.filter_by(extracted=False)
                
            conversations = (query.order_by(Conversation.started_at.desc())
                           .limit(limit)
                           .all())
                
            return [
                {
                    "conversation_id": conv.conversation_id,
                    "started_at": conv.started_at,
                    "ended_at": conv.ended_at,
                    "processed": conv.extracted
                }
                for conv in conversations
            ]
    
    def mark_conversation_processed(self, conversation_id: str) -> None:
        """Mark a conversation as processed."""
        if not validate_uuid(conversation_id):
            raise ValueError("Invalid conversation ID format")
            
        with db.session() as session:
            conv = session.query(Conversation).filter_by(conversation_id=conversation_id).first()
            if conv:
                conv.extracted = True
                
                # Mark any extraction jobs as completed
                jobs = session.query(ExtractionJob).filter_by(
                    conversation_id=conversation_id,
                    status="pending"
                ).all()
                
                for job in jobs:
                    job.status = "completed"
                    job.completed_at = int(datetime.now().timestamp())

# Create global API instance for easy import
api = CallistoAPI()