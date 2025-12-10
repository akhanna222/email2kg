"""
Pydantic schemas for authentication endpoints.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime


class UserRegister(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload data."""
    user_id: Optional[int] = None
    email: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user data response."""
    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    gmail_connected: bool
    preferences: Optional[Dict[str, Any]] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    last_sync: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str
    new_password: str = Field(..., min_length=8)


class PreferencesUpdate(BaseModel):
    """Schema for updating user preferences."""
    email_sync_limit: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum number of emails to sync (0 or None = unlimited)"
    )
