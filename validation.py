"""Data validation using Pydantic."""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator

class UserCreateModel(BaseModel):
    """Validation model for user creation."""
    name: str
    platform_name: str
    platform_username: str
    platform_specific_id: Optional[str] = None
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name must not be empty')
        return v.strip()
    
    @validator('platform_name', 'platform_username')
    def platform_info_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Platform information must not be empty')
        return v.strip()


class KnowledgeStoreModel(BaseModel):
    """Validation model for knowledge storage."""
    user_id: str
    category_name: str
    value: Any
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    source: str = "user_stated"
    
    @validator('user_id', 'category_name', 'source')
    def fields_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Field must not be empty')
        return v.strip()
    
    @validator('source')
    def source_must_be_valid(cls, v):
        valid_sources = ["user_stated", "extracted", "edited"]
        if v not in valid_sources:
            raise ValueError(f'Source must be one of {valid_sources}')
        return v


class CategoryCreateModel(BaseModel):
    """Validation model for category creation."""
    category_name: str
    data_type: str
    is_personal: bool = False
    
    @validator('category_name', 'data_type')
    def fields_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Field must not be empty')
        return v.strip()
    
    @validator('data_type')
    def data_type_must_be_valid(cls, v):
        valid_types = ["string", "list", "date", "number", "boolean"]
        if v not in valid_types:
            raise ValueError(f'Data type must be one of {valid_types}')
        return v


class MessageAddModel(BaseModel):
    """Validation model for adding messages."""
    conversation_id: str
    content: str
    is_from_user: bool