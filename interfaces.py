"""Abstract base classes defining the Callisto API interface."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

class UserInterface(ABC):
    """Interface for user management operations."""
    
    @abstractmethod
    def get_user(self, platform_name: str, platform_username: str) -> Optional[Any]:
        """Find a user by platform and username."""
        pass
    
    @abstractmethod
    def create_user(self, name: str, platform_name: str, platform_username: str, 
                   platform_specific_id: Optional[str] = None) -> Any:
        """Create a new user with platform association."""
        pass
    
    @abstractmethod
    def update_user(self, user_id: str, name: str) -> None:
        """Update user information."""
        pass
    
    @abstractmethod
    def delete_user(self, user_id: str) -> None:
        """Delete a user and all associated data."""
        pass
    
    @abstractmethod
    def link_platform(self, user_id: str, platform_name: str, platform_username: str,
                    platform_specific_id: Optional[str] = None) -> None:
        """Link a user to a platform."""
        pass


class KnowledgeInterface(ABC):
    """Interface for knowledge management operations."""
    
    @abstractmethod
    def get_user_knowledge(self, user_id: str) -> Dict[str, Any]:
        """Get all knowledge for a user, categorised."""
        pass
    
    @abstractmethod
    def store_knowledge(self, user_id: str, category_name: str, value: Any, 
                       confidence: float = 1.0, source: str = "user_stated") -> None:
        """Store a piece of knowledge about a user."""
        pass
    
    @abstractmethod
    def delete_knowledge(self, user_id: str, category_name: str) -> None:
        """Delete a piece of knowledge about a user."""
        pass
    
    @abstractmethod
    def get_knowledge_categories(self) -> List[Dict[str, Any]]:
        """Get all knowledge categories."""
        pass
    
    @abstractmethod
    def create_knowledge_category(self, category_name: str, data_type: str, 
                                is_personal: bool = False) -> None:
        """Create a new knowledge category."""
        pass


class ConversationInterface(ABC):
    """Interface for conversation management operations."""
    
    @abstractmethod
    def start_conversation(self, user_id: str, platform_name: str) -> str:
        """Start a new conversation and return the conversation ID."""
        pass
    
    @abstractmethod
    def add_message(self, conversation_id: str, content: str, is_from_user: bool) -> None:
        """Add a message to a conversation."""
        pass
    
    @abstractmethod
    def end_conversation(self, conversation_id: str) -> None:
        """End a conversation."""
        pass
    
    @abstractmethod
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a conversation."""
        pass


class CallistoAPIInterface(UserInterface, KnowledgeInterface, ConversationInterface):
    """Combined interface for all Callisto API operations."""
    pass