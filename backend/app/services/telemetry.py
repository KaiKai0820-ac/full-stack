"""Telemetry collection service for user sessions, device, and location tracking."""

import logging
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.models import (
    UserDeviceHistory,
    UserLocationHistory,
    UserProfile,
    UserSession,
)
from app.services.geolocation import geolocation_service

logger = logging.getLogger(__name__)


def validate_device_snapshot(device_snapshot: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and normalize device snapshot schema.
    
    Required fields: os_family, device_class
    Optional fields: os_version, screen_resolution, screen_density, viewport_width, viewport_height
    
    Args:
        device_snapshot: Raw device snapshot dictionary
        
    Returns:
        Validated and normalized device snapshot
        
    Raises:
        ValueError: If required fields are missing
    """
    if not isinstance(device_snapshot, dict):
        raise ValueError("device_snapshot must be a dictionary")

    # Check required fields
    if "os_family" not in device_snapshot or not device_snapshot["os_family"]:
        raise ValueError("os_family is required")
    if "device_class" not in device_snapshot or not device_snapshot["device_class"]:
        raise ValueError("device_class is required")

    # Normalize and set defaults for missing optional fields
    normalized = {
        "os_family": str(device_snapshot.get("os_family", "unknown")),
        "device_class": str(device_snapshot.get("device_class", "unknown")),
        "os_version": str(device_snapshot.get("os_version", "unknown")),
        "screen_resolution": str(device_snapshot.get("screen_resolution", "unknown")),
        "screen_density": float(device_snapshot.get("screen_density", 0.0)),
        "viewport_width": int(device_snapshot.get("viewport_width", 0)),
        "viewport_height": int(device_snapshot.get("viewport_height", 0)),
    }

    return normalized


def validate_location_snapshot(location_snapshot: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and normalize location snapshot schema.
    
    Required fields: country
    Optional fields: city, latitude, longitude, location_source
    
    Args:
        location_snapshot: Raw location snapshot dictionary
        
    Returns:
        Validated and normalized location snapshot
        
    Raises:
        ValueError: If required fields are missing
    """
    if not isinstance(location_snapshot, dict):
        raise ValueError("location_snapshot must be a dictionary")

    # Check required fields
    if "country" not in location_snapshot or not location_snapshot["country"]:
        raise ValueError("country is required in location_snapshot")

    # Normalize and set defaults
    normalized = {
        "country": str(location_snapshot.get("country", "Unknown")),
        "city": location_snapshot.get("city"),
        "latitude": float(location_snapshot["latitude"]) if location_snapshot.get("latitude") is not None else None,
        "longitude": float(location_snapshot["longitude"]) if location_snapshot.get("longitude") is not None else None,
        "location_source": str(location_snapshot.get("location_source", "IP")),
    }

    return normalized


def normalize_device_snapshot(device_snapshot: dict[str, Any] | None) -> dict[str, Any]:
    """
    Normalize device snapshot, marking missing fields as "unknown".
    
    Args:
        device_snapshot: Raw device snapshot or None
        
    Returns:
        Normalized device snapshot with all fields present
    """
    if not device_snapshot:
        return {
            "os_family": "unknown",
            "device_class": "unknown",
            "os_version": "unknown",
            "screen_resolution": "unknown",
            "screen_density": 0.0,
            "viewport_width": 0,
            "viewport_height": 0,
        }

    try:
        return validate_device_snapshot(device_snapshot)
    except (ValueError, KeyError, TypeError) as e:
        logger.warning(f"Invalid device snapshot, using defaults: {e}")
        return {
            "os_family": str(device_snapshot.get("os_family", "unknown")),
            "device_class": str(device_snapshot.get("device_class", "unknown")),
            "os_version": str(device_snapshot.get("os_version", "unknown")),
            "screen_resolution": str(device_snapshot.get("screen_resolution", "unknown")),
            "screen_density": float(device_snapshot.get("screen_density", 0.0)),
            "viewport_width": int(device_snapshot.get("viewport_width", 0)),
            "viewport_height": int(device_snapshot.get("viewport_height", 0)),
        }


def create_session(
    session: Session,
    user_id: str,
    ip_address: str,
    device_snapshot: dict[str, Any] | None = None,
    location_snapshot: dict[str, Any] | None = None,
    opt_out_flags: dict[str, Any] | None = None,
) -> UserSession:
    """
    Create a new user session with device and location snapshots.
    
    Args:
        session: Database session
        user_id: User profile ID (openid or UUID)
        ip_address: User's IP address
        device_snapshot: Device information snapshot
        location_snapshot: Location information snapshot (optional, will be enriched from IP if not provided)
        opt_out_flags: User opt-out preferences
        
    Returns:
        Created UserSession object
    """
    logger.info(f"Creating session for user {user_id} from IP {ip_address}")

    # Get or create user profile
    user_profile = get_or_create_user_profile(session, user_id)

    # Normalize device snapshot
    normalized_device = normalize_device_snapshot(device_snapshot)

    # Enrich location snapshot if not provided or if opt-out allows
    if location_snapshot is None:
        if opt_out_flags and opt_out_flags.get("location_tracking", False):
            normalized_location = {
                "country": "Unknown",
                "city": None,
                "latitude": None,
                "longitude": None,
                "location_source": "IP",
            }
        else:
            try:
                normalized_location = geolocation_service.enrich_location_snapshot(
                    ip_address, opt_out_flags
                )
            except Exception as e:
                logger.warning(f"Geolocation service unavailable, using default: {e}")
                normalized_location = {
                    "country": "Unknown",
                    "city": None,
                    "latitude": None,
                    "longitude": None,
                    "location_source": "IP",
                }
    else:
        try:
            normalized_location = validate_location_snapshot(location_snapshot)
        except (ValueError, KeyError, TypeError) as e:
            logger.warning(f"Invalid location snapshot, enriching from IP: {e}")
            normalized_location = geolocation_service.enrich_location_snapshot(
                ip_address, opt_out_flags
            )

    # Create session
    now = datetime.utcnow()
    user_session = UserSession(
        user_id=user_profile.id,
        start_timestamp=now,
        ip_address=ip_address,
        device_snapshot=normalized_device,
        location_snapshot=normalized_location,
    )
    session.add(user_session)
    session.commit()
    session.refresh(user_session)

    # Preserve device snapshot in history
    preserve_device_snapshot(session, user_profile.id, normalized_device, now)

    # Preserve location snapshot in history
    preserve_location_snapshot(
        session, user_profile.id, ip_address, normalized_location, now
    )

    # Update user profile last_active_at
    user_profile.last_active_at = now
    session.add(user_profile)
    session.commit()

    logger.info(f"Created session {user_session.id} for user {user_id}")
    return user_session


def update_session_end_time(
    session: Session, session_id: str, end_timestamp: datetime | None = None
) -> UserSession:
    """
    Update session end time and calculate duration.
    
    Args:
        session: Database session
        session_id: Session ID
        end_timestamp: End timestamp (defaults to now if not provided)
        
    Returns:
        Updated UserSession object
        
    Raises:
        ValueError: If session not found
    """
    statement = select(UserSession).where(UserSession.id == session_id)
    user_session = session.exec(statement).first()

    if not user_session:
        raise ValueError(f"Session {session_id} not found")

    end_time = end_timestamp or datetime.utcnow()
    user_session.end_timestamp = end_time

    # Calculate duration
    if user_session.start_timestamp:
        duration = int((end_time - user_session.start_timestamp).total_seconds())
        user_session.duration = duration

    session.add(user_session)
    session.commit()
    session.refresh(user_session)

    logger.info(f"Updated session {session_id} end time to {end_time}")
    return user_session


def get_or_create_user_profile(session: Session, user_id: str) -> UserProfile:
    """
    Get existing user profile by openid or create new one.
    
    Args:
        session: Database session
        user_id: User openid or UUID
        
    Returns:
        UserProfile object
    """
    # Try to find by openid first
    statement = select(UserProfile).where(UserProfile.openid == user_id)
    user_profile = session.exec(statement).first()

    if user_profile:
        return user_profile

    # Try to find by UUID
    try:
        import uuid
        user_uuid = uuid.UUID(user_id)
        statement = select(UserProfile).where(UserProfile.id == user_uuid)
        user_profile = session.exec(statement).first()
        if user_profile:
            return user_profile
    except ValueError:
        pass

    # Create new profile
    now = datetime.utcnow()
    user_profile = UserProfile(
        openid=user_id,
        registration_date=now,
        last_active_at=now,
    )
    session.add(user_profile)
    session.commit()
    session.refresh(user_profile)

    logger.info(f"Created new user profile {user_profile.id} for openid {user_id}")
    return user_profile


def preserve_device_snapshot(
    session: Session,
    user_id: str,
    device_snapshot: dict[str, Any],
    timestamp: datetime,
) -> None:
    """
    Preserve device snapshot in UserDeviceHistory.
    
    Args:
        session: Database session
        user_id: User profile UUID
        device_snapshot: Device snapshot dictionary
        timestamp: Timestamp when device was seen
    """
    import uuid
    user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

    # Find existing device history entry with same snapshot
    statement = select(UserDeviceHistory).where(
        UserDeviceHistory.user_id == user_uuid
    )
    existing_entries = session.exec(statement).all()

    # Check if we have a matching device snapshot
    matching_entry = None
    for entry in existing_entries:
        if entry.device_snapshot == device_snapshot:
            matching_entry = entry
            break

    if matching_entry:
        # Update existing entry
        matching_entry.last_seen_at = timestamp
        matching_entry.interaction_count += 1
        matching_entry.updated_at = datetime.utcnow()
        session.add(matching_entry)
    else:
        # Create new entry
        new_entry = UserDeviceHistory(
            user_id=user_uuid,
            device_snapshot=device_snapshot,
            first_seen_at=timestamp,
            last_seen_at=timestamp,
            interaction_count=1,
        )
        session.add(new_entry)

    session.commit()


def preserve_location_snapshot(
    session: Session,
    user_id: str,
    ip_address: str,
    location_snapshot: dict[str, Any],
    timestamp: datetime,
) -> None:
    """
    Preserve location snapshot in UserLocationHistory.
    
    Args:
        session: Database session
        user_id: User profile UUID
        ip_address: IP address
        location_snapshot: Location snapshot dictionary
        timestamp: Timestamp when location was seen
    """
    import uuid
    user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

    # Find existing location history entry with same IP and location
    statement = select(UserLocationHistory).where(
        UserLocationHistory.user_id == user_uuid,
        UserLocationHistory.ip_address == ip_address,
    )
    existing_entries = session.exec(statement).all()

    # Check if we have a matching location snapshot
    matching_entry = None
    for entry in existing_entries:
        if (
            entry.ip_derived_location.get("country") == location_snapshot.get("country")
            and entry.ip_derived_location.get("city") == location_snapshot.get("city")
        ):
            matching_entry = entry
            break

    if matching_entry:
        # Update existing entry
        matching_entry.last_seen_at = timestamp
        matching_entry.updated_at = datetime.utcnow()
        session.add(matching_entry)
    else:
        # Create new entry
        new_entry = UserLocationHistory(
            user_id=user_uuid,
            ip_address=ip_address,
            ip_derived_location={
                "country": location_snapshot.get("country", "Unknown"),
                "city": location_snapshot.get("city"),
            },
            precise_location=(
                {
                    "latitude": location_snapshot.get("latitude"),
                    "longitude": location_snapshot.get("longitude"),
                }
                if location_snapshot.get("latitude") and location_snapshot.get("longitude")
                else None
            ),
            location_source=location_snapshot.get("location_source", "IP"),
            first_seen_at=timestamp,
            last_seen_at=timestamp,
        )
        session.add(new_entry)

    session.commit()

