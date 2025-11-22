import uuid
from datetime import date, datetime, time
from typing import Any

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel, Column, JSON
from sqlalchemy import JSON as SA_JSON


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# ============================================================================
# UserInfo Report Models
# ============================================================================


class UserProfile(SQLModel, table=True):
    """User profile with immutable openid and mutable profile information."""
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    openid: str = Field(unique=True, index=True, max_length=255)
    nickname: str | None = Field(default=None, max_length=255)
    registration_date: datetime = Field(default_factory=datetime.utcnow)
    last_active_at: datetime | None = Field(default=None, index=True)
    opt_out_flags: dict[str, Any] | None = Field(default=None, sa_column=Column(SA_JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    sessions: list["UserSession"] = Relationship(back_populates="user_profile")
    ad_interactions: list["AdInteraction"] = Relationship(back_populates="user_profile")
    device_history: list["UserDeviceHistory"] = Relationship(back_populates="user_profile")
    location_history: list["UserLocationHistory"] = Relationship(back_populates="user_profile")
    activity_patterns: list["UserActivityPattern"] = Relationship(back_populates="user_profile")
    daily_metrics: list["DailyUserMetrics"] = Relationship(back_populates="user_profile")
    risk_audits: list["RiskDecisionAudit"] = Relationship(back_populates="user_profile")


class UserSession(SQLModel, table=True):
    """User session with device and location snapshots."""
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="userprofile.id", index=True)
    start_timestamp: datetime = Field(index=True)
    end_timestamp: datetime | None = Field(default=None)
    duration: int | None = Field(default=None)  # seconds
    ip_address: str = Field(max_length=45)  # IPv6 max length
    device_snapshot: dict[str, Any] | None = Field(default=None, sa_column=Column(SA_JSON))
    location_snapshot: dict[str, Any] | None = Field(default=None, sa_column=Column(SA_JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user_profile: UserProfile = Relationship(back_populates="sessions")
    ad_interactions: list["AdInteraction"] = Relationship(back_populates="session")


class AdInteraction(SQLModel, table=True):
    """Append-only event log for ad interactions."""
    
    __tablename__ = "ad_interaction"
    
    interaction_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="userprofile.id", index=True)
    session_id: uuid.UUID | None = Field(default=None, foreign_key="usersession.id", index=True)
    ad_type: str = Field(index=True, max_length=50)  # interstitial, reward, banner
    ad_creative_id: str = Field(index=True, max_length=255)
    placement_id: str = Field(max_length=255)
    action: str = Field(index=True, max_length=50)  # impression, click, skip, complete, dismiss, failure
    timestamp: datetime = Field(index=True)
    device_snapshot: dict[str, Any] | None = Field(default=None, sa_column=Column(SA_JSON))
    location_snapshot: dict[str, Any] | None = Field(default=None, sa_column=Column(SA_JSON))
    metadata: dict[str, Any] | None = Field(default=None, sa_column=Column(SA_JSON))
    schema_version: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user_profile: UserProfile = Relationship(back_populates="ad_interactions")
    session: UserSession | None = Relationship(back_populates="ad_interactions")


class UserDeviceHistory(SQLModel, table=True):
    """Tracks device information changes over time."""
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="userprofile.id")
    device_snapshot: dict[str, Any] = Field(sa_column=Column(SA_JSON))
    first_seen_at: datetime
    last_seen_at: datetime
    interaction_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user_profile: UserProfile = Relationship(back_populates="device_history")


class UserLocationHistory(SQLModel, table=True):
    """Tracks location information changes over time."""
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="userprofile.id")
    ip_address: str = Field(index=True, max_length=45)
    ip_derived_location: dict[str, Any] = Field(sa_column=Column(SA_JSON))
    precise_location: dict[str, Any] | None = Field(default=None, sa_column=Column(SA_JSON))
    location_source: str = Field(max_length=20)  # "IP" or "precise"
    first_seen_at: datetime
    last_seen_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user_profile: UserProfile = Relationship(back_populates="location_history")


class UserActivityPattern(SQLModel, table=True):
    """Aggregated time-based activity data per user."""
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="userprofile.id")
    hour_of_day: int = Field(ge=0, le=23)
    day_of_week: int = Field(ge=0, le=6)  # 0=Monday
    average_session_start_time: time | None = Field(default=None)
    average_session_duration: int | None = Field(default=None)  # seconds
    total_sessions: int = Field(default=0)
    most_active_periods: list[dict[str, Any]] | None = Field(default=None, sa_column=Column(SA_JSON))
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user_profile: UserProfile = Relationship(back_populates="activity_patterns")


class DailyUserMetrics(SQLModel, table=True):
    """Daily aggregated metrics per user."""
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="userprofile.id", index=True)
    date: date = Field(index=True)
    total_impressions: int = Field(default=0)
    total_clicks: int = Field(default=0)
    total_completions: int = Field(default=0)
    total_skips: int = Field(default=0)
    ctr: float | None = Field(default=None, ge=0, le=1)  # Click-through rate
    completion_rate: float | None = Field(default=None, ge=0, le=1)
    skip_ratio: float | None = Field(default=None, ge=0, le=1)
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user_profile: UserProfile = Relationship(back_populates="daily_metrics")


class DailyCampaignMetrics(SQLModel, table=True):
    """Daily aggregated metrics per campaign/ad creative."""
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    campaign_id: str = Field(index=True, max_length=255)
    date: date = Field(index=True)
    total_impressions: int = Field(default=0)
    total_clicks: int = Field(default=0)
    total_completions: int = Field(default=0)
    total_skips: int = Field(default=0)
    ctr: float | None = Field(default=None, ge=0, le=1)
    completion_rate: float | None = Field(default=None, ge=0, le=1)
    skip_ratio: float | None = Field(default=None, ge=0, le=1)
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RiskDecisionAudit(SQLModel, table=True):
    """Audit log for risk scoring and fraud detection decisions."""
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="userprofile.id", index=True)
    risk_score: float = Field(ge=0, le=100)
    triggering_factors: dict[str, Any] | None = Field(default=None, sa_column=Column(SA_JSON))
    mitigation_action: str = Field(max_length=50)  # observation, rate_limit, shadow_ban, suspension
    action_duration: int | None = Field(default=None)  # seconds
    decision_timestamp: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user_profile: UserProfile = Relationship(back_populates="risk_audits")
