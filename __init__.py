"""Callisto memory database module for Jupiter AI."""
from .db import db
from .models import (
    User, Platform, UserPlatform,
    KnowledgeCategory, UserKnowledge,
    Conversation, Message, ExtractionJob
)
from .api import api
from .security import sanitize_input, validate_uuid, secure_delete

__all__ = [
    'db', 'initialize', 'api',
    'User', 'Platform', 'UserPlatform',
    'KnowledgeCategory', 'UserKnowledge',
    'Conversation', 'Message', 'ExtractionJob',
    'sanitize_input', 'validate_uuid', 'secure_delete'
]

def initialize(db_path=None):
    """Initialize Callisto database."""
    if db_path:
        global db
        from .db import Database
        db = Database(db_path)
    
    # Create tables
    db.init_db()
    
    # Add default data
    db.init_default_data()
    
    return db