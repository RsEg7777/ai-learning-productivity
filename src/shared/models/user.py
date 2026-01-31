"""User-related data models."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class UserPreferences(BaseModel):
    """User preferences and settings."""
    language: str = Field(default="en", description="Preferred language code")
    voice_enabled: bool = Field(default=False, description="Enable voice interface")
    voice_id: Optional[str] = Field(None, description="Preferred voice ID for TTS")
    theme: str = Field(default="light", description="UI theme preference")
    notification_enabled: bool = Field(default=True, description="Enable notifications")
    spaced_repetition_enabled: bool = Field(default=True, description="Enable spaced repetition")
    daily_goal_minutes: int = Field(default=30, ge=0, description="Daily study goal in minutes")


class Achievement(BaseModel):
    """User achievement."""
    id: str = Field(..., description="Achievement identifier")
    name: str = Field(..., description="Achievement name")
    description: str = Field(..., description="Achievement description")
    earned_at: datetime = Field(..., description="When achievement was earned")
    icon: Optional[str] = Field(None, description="Icon identifier")


class LearningProgress(BaseModel):
    """User's learning progress and statistics."""
    user_id: str = Field(..., description="User identifier")
    total_study_time: int = Field(default=0, ge=0, description="Total study time in minutes")
    content_processed: int = Field(default=0, ge=0, description="Number of content items processed")
    quizzes_completed: int = Field(default=0, ge=0, description="Number of quizzes completed")
    average_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Average quiz score")
    streak_days: int = Field(default=0, ge=0, description="Current study streak in days")
    achievements: List[Achievement] = Field(default_factory=list, description="Earned achievements")
    last_active: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")


class User(BaseModel):
    """User account information."""
    id: str = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User email address")
    username: Optional[str] = Field(None, description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    preferences: UserPreferences = Field(
        default_factory=UserPreferences,
        description="User preferences"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")
    last_active: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    is_active: bool = Field(default=True, description="Account active status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class UserRegistration(BaseModel):
    """User registration data."""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    username: Optional[str] = Field(None, description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    preferred_language: str = Field(default="en", description="Preferred language")


class LoginCredentials(BaseModel):
    """Login credentials."""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")
    mfa_code: Optional[str] = Field(None, description="Multi-factor authentication code")


class AuthResult(BaseModel):
    """Authentication result."""
    success: bool = Field(..., description="Authentication success status")
    user_id: Optional[str] = Field(None, description="User identifier if successful")
    access_token: Optional[str] = Field(None, description="Access token")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    requires_mfa: bool = Field(default=False, description="Whether MFA is required")
