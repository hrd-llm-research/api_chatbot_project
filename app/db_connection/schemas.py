from pydantic import BaseModel, Field, field_validator
import re 
from fastapi import HTTPException
from datetime import datetime
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str
    
class TokenData(BaseModel):
    email: str | None = None

""""
    User model
"""
class User(BaseModel):
    username: str | None = Field(
        min_length=2,
        max_length=30,
    )
    email: str | None = Field(
        default="string",
        pattern=r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.\w+$',
    )
    
    class Config:
        from_attributes = True

class UserResponse(User):
    id: int
    is_active: bool

class UserCreate(User):
    password: str | None = Field(
        default="string",
        min_length=8,
        description="Password must contain at least 8 characters, one uppercase, one lowercase, one number, and one special character",
    )
    
    @field_validator("password")
    def validate_password(cls, value):
        if not any(char.isupper() for char in value):
            raise HTTPException(status_code=422, detail="Password must contain at least one uppercase letter")
        if not any(char.islower() for char in value):
            raise HTTPException(status_code=422, detail="Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in value):
            raise HTTPException(status_code=422, detail="Password must contain at least one digit")
        if not any(char in "@$!%*?&" for char in value):
            raise HTTPException(status_code=422, detail="Password must contain at least one special character")
        return value
  
class ThirdPartyUserCreate(User):
    image: str | None
    sub: str
    
      
class FileSchemaDB(BaseModel):
    id: int
    session_id: int = Field(
        ..., ge=1,
        description="Session ID must be a positive integer"
    )
    collection_name: str = Field(
        ..., min_length=2,
        description="Collection name must be at least 2 characters long"
    )
    file_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True
    
class MessageHistoryCreate(BaseModel):
    session_id: int
    history_name: str
    
class ChatModel(BaseModel):
    file_record: object
    collection_name: str
    chroma_db: str
    
class ProjectDescription(BaseModel):
    description: str = Field(
        default="string",
        min_length=2,
        description="Description must be at least 10 characters long"
    )

class ModelCustomizationCreate(BaseModel):
    model_id: int = Field(...)
    provider_api_key: Optional[str] = None  
    temperature: float = Field(...)
    max_token: int = Field(..., ge=1)
    
class ExternalChatbotSchema(BaseModel):
    input: str = Field(...)
    external_session_id: int = Field(..., ge=1)
    project_id: int = Field(..., ge=1)
    
class ChatbotPlaygroundSchema(BaseModel):
    input: str = Field(...)
    user_id: int = Field(..., ge=1)
    session_id: int = Field(..., ge=1)
    file_id: Optional[int] = None   
    
class TexBotSchema(BaseModel):
    input: str = Field(...)
    session_id: int = Field(..., ge=1)
    
class SuggestionBotSchema(BaseModel):
    user_id: int = Field(...)
    session_id: int = Field(...)
    file_id: Optional[int] = None  