"""Conversation management for Callisto."""
from typing import Dict, List, Optional, Any

from .db import db
from .models import Conversation, Message

class ConversationManager:
    """Handles conversation operations."""
    
    @staticmethod
    def get_conversation_history(conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a conversation."""
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
    
    @staticmethod
    def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific conversation by ID."""
        with db.session() as session:
            conv = session.query(Conversation).filter_by(conversation_id=conversation_id).first()
            if not conv:
                return None
                
            # Get message count
            message_count = session.query(Message).filter_by(conversation_id=conversation_id).count()
            
            return {
                "conversation_id": conv.conversation_id,
                "user_id": conv.user_id,
                "started_at": conv.started_at,
                "ended_at": conv.ended_at,
                "processed": conv.extracted,
                "message_count": message_count
            }