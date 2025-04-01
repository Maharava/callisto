"""Knowledge management operations for Callisto."""
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

from sqlalchemy import and_, or_

from .db import db
from .models import UserKnowledge, KnowledgeCategory, User
from .security import sanitize_input

class KnowledgeManager:
    """Handles knowledge storage and retrieval operations."""

    @staticmethod
    def get_knowledge(user_id: str, category_name: Optional[str] = None, 
                     is_personal: Optional[bool] = None) -> Dict[str, Any]:
        """Get user knowledge with optional filtering."""
        with db.session() as session:
            query = (session.query(UserKnowledge, KnowledgeCategory)
                    .join(KnowledgeCategory)
                    .filter(UserKnowledge.user_id == user_id))
            
            # Apply filters if provided
            if category_name:
                query = query.filter(KnowledgeCategory.category_name == category_name)
            if is_personal is not None:
                query = query.filter(KnowledgeCategory.is_personal == is_personal)
                
            knowledge_items = query.all()
            
            result = {}
            for knowledge, category in knowledge_items:
                # Convert value based on data type
                value = KnowledgeManager._convert_value(knowledge.value, category.data_type)
                    
                if category.category_name not in result:
                    result[category.category_name] = {
                        "value": value,
                        "confidence": knowledge.confidence,
                        "source": knowledge.source,
                        "is_personal": category.is_personal,
                        "updated_at": knowledge.updated_at
                    }
                elif knowledge.confidence > result[category.category_name]["confidence"]:
                    # Keep the highest confidence value
                    result[category.category_name] = {
                        "value": value,
                        "confidence": knowledge.confidence,
                        "source": knowledge.source,
                        "is_personal": category.is_personal,
                        "updated_at": knowledge.updated_at
                    }
            
            return result
    
    @staticmethod
    def _convert_value(value_str: str, data_type: str) -> Any:
        """Convert stored string to appropriate type."""
        if data_type == "list":
            try:
                return json.loads(value_str)
            except:
                return value_str
        elif data_type == "number":
            try:
                return float(value_str)
            except:
                return value_str
        elif data_type == "boolean":
            return value_str.lower() in ('true', 'yes', '1')
        else:
            return value_str
            
    @staticmethod
    def store_knowledge(user_id: str, category_name: str, value: Any, 
                       confidence: float = 1.0, source: str = "user_stated") -> None:
        """Store a piece of knowledge about a user."""
        # Sanitize category name
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
                # Create new category if it doesn't exist
                data_type = KnowledgeManager._detect_data_type(value)
                category = KnowledgeCategory(
                    category_name=category_name,
                    data_type=data_type,
                    is_personal=False
                )
                session.add(category)
                session.flush()
            
            # Convert value to string
            value_str = KnowledgeManager._convert_to_storage_format(value, category.data_type)
            
            now = int(datetime.now().timestamp())
            
            # Create or update knowledge
            knowledge = (session.query(UserKnowledge)
                .filter_by(user_id=user_id, category_id=category.category_id)
                .first())
                
            if knowledge:
                # Only update if new confidence is higher or equal
                if confidence >= knowledge.confidence:
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
    
    @staticmethod
    def _detect_data_type(value: Any) -> str:
        """Determine the data type based on the value."""
        if isinstance(value, list):
            return "list"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, (int, float)):
            return "number"
        else:
            return "string"
    
    @staticmethod
    def _convert_to_storage_format(value: Any, data_type: str) -> str:
        """Convert value to storage format based on data type."""
        if data_type == "list" and not isinstance(value, str):
            return json.dumps(value)
        else:
            return str(value)
            
    @staticmethod
    def batch_store_knowledge(user_id: str, knowledge_items: List[Dict[str, Any]]) -> None:
        """Store multiple knowledge items at once."""
        for item in knowledge_items:
            KnowledgeManager.store_knowledge(
                user_id=user_id,
                category_name=item["category"],
                value=item["value"],
                confidence=item.get("confidence", 1.0),
                source=item.get("source", "user_stated")
            )
    
    @staticmethod
    def delete_knowledge(user_id: str, category_name: str) -> None:
        """Delete a piece of knowledge about a user."""
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
                session.delete(knowledge)
                
    @staticmethod
    def merge_knowledge(user_id: str, target_user_id: str) -> None:
        """Merge knowledge from target user into this user."""
        target_knowledge = KnowledgeManager.get_knowledge(target_user_id)
        
        for category, data in target_knowledge.items():
            # Only merge if we don't have higher confidence data
            existing = KnowledgeManager.get_knowledge(user_id, category)
            if not existing or existing.get(category, {}).get("confidence", 0) < data["confidence"]:
                KnowledgeManager.store_knowledge(
                    user_id=user_id,
                    category_name=category,
                    value=data["value"],
                    confidence=data["confidence"],
                    source=data["source"]
                )
                
    @staticmethod
    def get_knowledge_by_source(user_id: str, source: str) -> Dict[str, Any]:
        """Get all knowledge from a specific source."""
        with db.session() as session:
            knowledge_items = (session.query(UserKnowledge, KnowledgeCategory)
                .join(KnowledgeCategory)
                .filter(UserKnowledge.user_id == user_id, UserKnowledge.source == source)
                .all())
            
            result = {}
            for knowledge, category in knowledge_items:
                value = KnowledgeManager._convert_value(knowledge.value, category.data_type)
                result[category.category_name] = {
                    "value": value,
                    "confidence": knowledge.confidence,
                    "is_personal": category.is_personal,
                    "updated_at": knowledge.updated_at
                }
            
            return result