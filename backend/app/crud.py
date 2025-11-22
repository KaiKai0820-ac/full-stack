import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    Item,
    ItemCreate,
    User,
    UserCreate,
    UserUpdate,
    UserProfile,
    UserSession,
    UserDeviceHistory,
    UserLocationHistory,
    AdInteraction,
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


# ============================================================================
# UserInfo Report CRUD Operations
# ============================================================================


def create_user_profile(*, session: Session, openid: str, nickname: str | None = None) -> UserProfile:
    """Create a new user profile."""
    user_profile = UserProfile(
        openid=openid,
        nickname=nickname,
        registration_date=datetime.utcnow(),
        last_active_at=datetime.utcnow(),
    )
    session.add(user_profile)
    session.commit()
    session.refresh(user_profile)
    return user_profile


def get_user_profile_by_openid(*, session: Session, openid: str) -> UserProfile | None:
    """Get user profile by openid."""
    statement = select(UserProfile).where(UserProfile.openid == openid)
    return session.exec(statement).first()


def get_user_profile_by_id(*, session: Session, user_id: uuid.UUID) -> UserProfile | None:
    """Get user profile by ID."""
    statement = select(UserProfile).where(UserProfile.id == user_id)
    return session.exec(statement).first()


def update_user_profile(
    *, session: Session, db_user_profile: UserProfile, nickname: str | None = None, opt_out_flags: dict | None = None
) -> UserProfile:
    """Update user profile."""
    if nickname is not None:
        db_user_profile.nickname = nickname
    if opt_out_flags is not None:
        db_user_profile.opt_out_flags = opt_out_flags
    db_user_profile.updated_at = datetime.utcnow()
    session.add(db_user_profile)
    session.commit()
    session.refresh(db_user_profile)
    return db_user_profile


def create_user_session(
    *, session: Session, user_id: uuid.UUID, start_timestamp: datetime, ip_address: str,
    device_snapshot: dict | None = None, location_snapshot: dict | None = None
) -> UserSession:
    """Create a new user session."""
    user_session = UserSession(
        user_id=user_id,
        start_timestamp=start_timestamp,
        ip_address=ip_address,
        device_snapshot=device_snapshot,
        location_snapshot=location_snapshot,
    )
    session.add(user_session)
    session.commit()
    session.refresh(user_session)
    return user_session


def get_user_session_by_id(*, session: Session, session_id: uuid.UUID) -> UserSession | None:
    """Get user session by ID."""
    statement = select(UserSession).where(UserSession.id == session_id)
    return session.exec(statement).first()


def update_user_session(
    *, session: Session, db_session: UserSession, end_timestamp: datetime | None = None
) -> UserSession:
    """Update user session end time and duration."""
    if end_timestamp:
        db_session.end_timestamp = end_timestamp
        if db_session.start_timestamp:
            duration = int((end_timestamp - db_session.start_timestamp).total_seconds())
            db_session.duration = duration
    
    session.add(db_session)
    session.commit()
    session.refresh(db_session)
    return db_session


def create_user_device_history(
    *, session: Session, user_id: uuid.UUID, device_snapshot: dict, first_seen_at: datetime, last_seen_at: datetime
) -> UserDeviceHistory:
    """Create a new device history entry."""
    device_history = UserDeviceHistory(
        user_id=user_id,
        device_snapshot=device_snapshot,
        first_seen_at=first_seen_at,
        last_seen_at=last_seen_at,
        interaction_count=1,
    )
    session.add(device_history)
    session.commit()
    session.refresh(device_history)
    return device_history


def get_user_device_history(*, session: Session, user_id: uuid.UUID) -> list[UserDeviceHistory]:
    """Get all device history entries for a user."""
    statement = select(UserDeviceHistory).where(UserDeviceHistory.user_id == user_id).order_by(UserDeviceHistory.last_seen_at.desc())
    return list(session.exec(statement).all())


def update_user_device_history(
    *, session: Session, db_device_history: UserDeviceHistory, last_seen_at: datetime
) -> UserDeviceHistory:
    """Update device history entry."""
    db_device_history.last_seen_at = last_seen_at
    db_device_history.interaction_count += 1
    db_device_history.updated_at = datetime.utcnow()
    session.add(db_device_history)
    session.commit()
    session.refresh(db_device_history)
    return db_device_history


def create_user_location_history(
    *, session: Session, user_id: uuid.UUID, ip_address: str, ip_derived_location: dict,
    precise_location: dict | None = None, location_source: str = "IP", first_seen_at: datetime, last_seen_at: datetime
) -> UserLocationHistory:
    """Create a new location history entry."""
    location_history = UserLocationHistory(
        user_id=user_id,
        ip_address=ip_address,
        ip_derived_location=ip_derived_location,
        precise_location=precise_location,
        location_source=location_source,
        first_seen_at=first_seen_at,
        last_seen_at=last_seen_at,
    )
    session.add(location_history)
    session.commit()
    session.refresh(location_history)
    return location_history


def get_user_location_history(*, session: Session, user_id: uuid.UUID) -> list[UserLocationHistory]:
    """Get all location history entries for a user."""
    statement = select(UserLocationHistory).where(UserLocationHistory.user_id == user_id).order_by(UserLocationHistory.last_seen_at.desc())
    return list(session.exec(statement).all())


def update_user_location_history(
    *, session: Session, db_location_history: UserLocationHistory, last_seen_at: datetime
) -> UserLocationHistory:
    """Update location history entry."""
    db_location_history.last_seen_at = last_seen_at
    db_location_history.updated_at = datetime.utcnow()
    session.add(db_location_history)
    session.commit()
    session.refresh(db_location_history)
    return db_location_history


# ============================================================================
# AdInteraction CRUD Operations (Append-only pattern)
# ============================================================================


def create_ad_interaction(*, session: Session, interaction: AdInteraction) -> AdInteraction:
    """
    Create a new ad interaction (append-only pattern, no updates/deletes).
    
    Note: This is a low-level CRUD function. Use app.services.interactions.log_ad_interaction
    for business logic and validation.
    """
    session.add(interaction)
    session.commit()
    session.refresh(interaction)
    return interaction


def get_ad_interaction(*, session: Session, interaction_id: uuid.UUID) -> AdInteraction | None:
    """Get an ad interaction by ID."""
    return session.get(AdInteraction, interaction_id)


def get_ad_interactions(
    *,
    session: Session,
    user_id: uuid.UUID | None = None,
    session_id: uuid.UUID | None = None,
    ad_type: str | None = None,
    action: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AdInteraction]:
    """
    Get ad interactions with optional filtering.
    
    Note: This function does NOT support updates or deletes (append-only pattern).
    """
    statement = select(AdInteraction)
    
    if user_id:
        statement = statement.where(AdInteraction.user_id == user_id)
    if session_id:
        statement = statement.where(AdInteraction.session_id == session_id)
    if ad_type:
        statement = statement.where(AdInteraction.ad_type == ad_type)
    if action:
        statement = statement.where(AdInteraction.action == action)
    
    statement = statement.order_by(AdInteraction.timestamp.desc()).limit(limit).offset(offset)
    
    return list(session.exec(statement).all())
