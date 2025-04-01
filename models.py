"""SQLAlchemy models for Callisto memory database."""
from datetime import datetime
import uuid
from sqlalchemy import Boolean, Column, ForeignKey, Integer, Float, String, Text, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    """User model storing core identity information."""
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True)
    name = Column(Text, nullable=False)
    created_at = Column(Integer, nullable=False)
    last_seen = Column(Integer, nullable=False)
    metadata = Column(Text)  # JSON for extensibility
    
    platforms = relationship("UserPlatform", back_populates="user", cascade="all, delete-orphan")
    knowledge = relationship("UserKnowledge", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

    @classmethod
    def create(cls, name, metadata=None):
        """Create a new user with generated UUID and timestamps."""
        now = int(datetime.now().timestamp())
        return cls(
            user_id=str(uuid.uuid4()),
            name=name,
            created_at=now,
            last_seen=now,
            metadata=metadata
        )


class Platform(Base):
    """Platform model for different interfaces (GUI, Discord, etc.)"""
    __tablename__ = "platforms"
    
    platform_id = Column(Integer, primary_key=True, autoincrement=True)
    platform_name = Column(Text, unique=True, nullable=False)
    
    users = relationship("UserPlatform", back_populates="platform")


class UserPlatform(Base):
    """Mapping between users and platforms with platform-specific identifiers."""
    __tablename__ = "user_platforms"
    
    mapping_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.platform_id"), nullable=False)
    platform_username = Column(Text, nullable=False)
    platform_specific_id = Column(Text)
    last_active = Column(Integer, nullable=False)
    
    user = relationship("User", back_populates="platforms")
    platform = relationship("Platform", back_populates="users")
    
    __table_args__ = (
        UniqueConstraint("platform_id", "platform_username"),
        UniqueConstraint("platform_id", "platform_specific_id"),
        Index("idx_userplatforms_user_id", "user_id")
    )


class KnowledgeCategory(Base):
    """Categories of knowledge that can be stored about users."""
    __tablename__ = "knowledge_categories"
    
    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(Text, unique=True, nullable=False)
    data_type = Column(Text, nullable=False)  # string, list, date, etc.
    is_personal = Column(Boolean, nullable=False, default=False)
    
    knowledge_items = relationship("UserKnowledge", back_populates="category")


class UserKnowledge(Base):
    """Knowledge items stored about specific users."""
    __tablename__ = "user_knowledge"
    
    knowledge_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    category_id = Column(Integer, ForeignKey("knowledge_categories.category_id"), nullable=False)
    value = Column(Text, nullable=False)  # JSON for complex types
    confidence = Column(Float, nullable=False, default=1.0)
    source = Column(Text, nullable=False)  # user_stated, extracted, edited
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer, nullable=False)
    
    user = relationship("User", back_populates="knowledge")
    category = relationship("KnowledgeCategory", back_populates="knowledge_items")
    
    __table_args__ = (
        Index("idx_userknowledge_user_id", "user_id"),
        Index("idx_userknowledge_category", "category_id")
    )


class Conversation(Base):
    """Record of conversations with users."""
    __tablename__ = "conversations"
    
    conversation_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.platform_id"), nullable=False)
    started_at = Column(Integer, nullable=False)
    ended_at = Column(Integer)  # NULL if ongoing
    extracted = Column(Boolean, nullable=False, default=False)
    
    user = relationship("User", back_populates="conversations")
    platform = relationship("Platform")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    extraction_jobs = relationship("ExtractionJob", back_populates="conversation", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_conversations_user_id", "user_id"),
        Index("idx_conversations_extracted", "extracted")
    )
    
    @classmethod
    def create(cls, user_id, platform_id):
        """Create a new conversation with generated UUID and timestamp."""
        now = int(datetime.now().timestamp())
        return cls(
            conversation_id=str(uuid.uuid4()),
            user_id=user_id,
            platform_id=platform_id,
            started_at=now
        )


class Message(Base):
    """Individual messages within a conversation."""
    __tablename__ = "messages"
    
    message_id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, ForeignKey("conversations.conversation_id"), nullable=False)
    is_from_user = Column(Boolean, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(Integer, nullable=False)
    
    conversation = relationship("Conversation", back_populates="messages")
    
    __table_args__ = (
        Index("idx_messages_conversation", "conversation_id"),
    )


class ExtractionJob(Base):
    """Scheduled jobs to extract knowledge from conversations."""
    __tablename__ = "extraction_jobs"
    
    job_id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, ForeignKey("conversations.conversation_id"), nullable=False)
    status = Column(Text, nullable=False)  # pending, processing, completed, failed
    created_at = Column(Integer, nullable=False)
    completed_at = Column(Integer)  # NULL if not completed
    error = Column(Text)  # NULL if no error
    
    conversation = relationship("Conversation", back_populates="extraction_jobs")
