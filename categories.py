"""Category management for Callisto."""
from typing import Dict, List, Any, Optional

from .db import db
from .models import KnowledgeCategory
from .security import sanitize_input

class CategoryManager:
    """Handles knowledge category operations."""
    
    VALID_DATA_TYPES = ["string", "list", "date", "number", "boolean"]
    
    @staticmethod
    def get_categories(include_personal: bool = True) -> List[Dict[str, Any]]:
        """Get all knowledge categories."""
        with db.session() as session:
            query = session.query(KnowledgeCategory)
            if not include_personal:
                query = query.filter(KnowledgeCategory.is_personal == False)
                
            categories = query.all()
            return [
                {
                    "category_name": cat.category_name,
                    "data_type": cat.data_type,
                    "is_personal": cat.is_personal
                }
                for cat in categories
            ]
    
    @staticmethod
    def create_category(category_name: str, data_type: str, is_personal: bool = False) -> bool:
        """Create a new knowledge category."""
        # Validate data_type
        if data_type not in CategoryManager.VALID_DATA_TYPES:
            raise ValueError(f"Data type must be one of {CategoryManager.VALID_DATA_TYPES}")
        
        # Sanitize inputs
        category_name = sanitize_input(category_name)
        
        with db.session() as session:
            # Check if category already exists
            existing = session.query(KnowledgeCategory).filter_by(category_name=category_name).first()
            if existing:
                return False
                
            category = KnowledgeCategory(
                category_name=category_name,
                data_type=data_type,
                is_personal=is_personal
            )
            session.add(category)
            return True
    
    @staticmethod
    def update_category(category_name: str, data_type: Optional[str] = None, 
                      is_personal: Optional[bool] = None) -> bool:
        """Update an existing knowledge category."""
        # Validate data_type if provided
        if data_type and data_type not in CategoryManager.VALID_DATA_TYPES:
            raise ValueError(f"Data type must be one of {CategoryManager.VALID_DATA_TYPES}")
        
        # Sanitize inputs
        category_name = sanitize_input(category_name)
        
        with db.session() as session:
            category = session.query(KnowledgeCategory).filter_by(category_name=category_name).first()
            if not category:
                return False
                
            if data_type:
                category.data_type = data_type
            if is_personal is not None:
                category.is_personal = is_personal
                
            return True
    
    @staticmethod
    def delete_category(category_name: str) -> bool:
        """Delete a knowledge category."""
        category_name = sanitize_input(category_name)
        
        with db.session() as session:
            category = session.query(KnowledgeCategory).filter_by(category_name=category_name).first()
            if not category:
                return False
                
            session.delete(category)
            return True
    
    @staticmethod
    def get_category(category_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific category by name."""
        category_name = sanitize_input(category_name)
        
        with db.session() as session:
            category = session.query(KnowledgeCategory).filter_by(category_name=category_name).first()
            if not category:
                return None
                
            return {
                "category_name": category.category_name,
                "data_type": category.data_type,
                "is_personal": category.is_personal
            }
            
    @staticmethod
    def create_default_categories() -> None:
        """Create default knowledge categories."""
        default_categories = [
            {"category_name": "location", "data_type": "string", "is_personal": True},
            {"category_name": "likes", "data_type": "list", "is_personal": False},
            {"category_name": "dislikes", "data_type": "list", "is_personal": False},
            {"category_name": "birthday", "data_type": "date", "is_personal": True},
            {"category_name": "occupation", "data_type": "string", "is_personal": False},
            {"category_name": "interests", "data_type": "list", "is_personal": False},
            {"category_name": "preferences", "data_type": "list", "is_personal": False},
            {"category_name": "family", "data_type": "list", "is_personal": True},
        ]
        
        for cat in default_categories:
            CategoryManager.create_category(**cat)