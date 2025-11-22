"""Ad interaction logging service for tracking impressions, clicks, skips, completions, dismissals, and failures."""

import logging
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.models import AdInteraction, UserSession

logger = logging.getLogger(__name__)

# Valid action types
VALID_ACTIONS = {"impression", "click", "skip", "complete", "dismiss", "failure"}

# Valid ad types
VALID_AD_TYPES = {"interstitial", "reward", "banner"}

# Schema version for append-only event logging
CURRENT_SCHEMA_VERSION = 1


def validate_action_type(action: str) -> None:
    """Validate that action is one of the valid action types."""
    if action not in VALID_ACTIONS:
        raise ValueError(f"Invalid action type: {action}. Must be one of: {', '.join(VALID_ACTIONS)}")


def validate_ad_type(ad_type: str) -> None:
    """Validate that ad_type is one of the valid ad types."""
    if ad_type not in VALID_AD_TYPES:
        raise ValueError(f"Invalid ad type: {ad_type}. Must be one of: {', '.join(VALID_AD_TYPES)}")


def validate_metadata_structure(action: str, metadata: dict[str, Any] | None) -> dict[str, Any]:
    """
    Validate metadata structure based on action type.
    
    Args:
        action: Action type (impression, click, skip, complete, dismiss, failure)
        metadata: Metadata dictionary to validate
        
    Returns:
        Validated metadata dictionary
        
    Raises:
        ValueError: If metadata structure is invalid for the action type
    """
    if metadata is None:
        metadata = {}
    
    if action == "click":
        # Click metadata: time_since_impression (seconds), click_position (for banners)
        if "time_since_impression" not in metadata:
            logger.warning("click action missing time_since_impression, defaulting to 0")
            metadata["time_since_impression"] = 0
        if "click_position" not in metadata:
            metadata["click_position"] = None
    elif action in ("skip", "dismiss"):
        # Skip/dismiss metadata: time_watched (seconds), skip_reason (optional)
        if "time_watched" not in metadata:
            logger.warning(f"{action} action missing time_watched, defaulting to 0")
            metadata["time_watched"] = 0
        if "skip_reason" not in metadata:
            metadata["skip_reason"] = None
    elif action == "complete":
        # Completion metadata: total_watch_duration, reward_type, reward_amount, verification_status
        if "total_watch_duration" not in metadata:
            logger.warning("complete action missing total_watch_duration, defaulting to 0")
            metadata["total_watch_duration"] = 0
        if "reward_type" not in metadata:
            metadata["reward_type"] = None
        if "reward_amount" not in metadata:
            metadata["reward_amount"] = None
        if "verification_status" not in metadata:
            metadata["verification_status"] = "pending"
    elif action == "failure":
        # Failure metadata: error_code, error_message
        if "error_code" not in metadata:
            logger.warning("failure action missing error_code, defaulting to 'unknown'")
            metadata["error_code"] = "unknown"
        if "error_message" not in metadata:
            metadata["error_message"] = None
    
    return metadata


def capture_device_location_snapshots(
    session: Session, user_session_id: str | None
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """
    Capture device and location snapshots at interaction time.
    
    Preserves historical context even if device/location changes later.
    
    Args:
        session: Database session
        user_session_id: Optional session ID to get snapshots from
        
    Returns:
        Tuple of (device_snapshot, location_snapshot)
    """
    device_snapshot = None
    location_snapshot = None
    
    if user_session_id:
        try:
            import uuid
            session_uuid = uuid.UUID(user_session_id)
            user_session = session.get(UserSession, session_uuid)
            if user_session:
                device_snapshot = user_session.device_snapshot
                location_snapshot = user_session.location_snapshot
        except (ValueError, Exception) as e:
            logger.warning(f"Failed to get snapshots from session {user_session_id}: {e}")
    
    return device_snapshot, location_snapshot


def log_ad_interaction(
    session: Session,
    user_id: str,
    ad_type: str,
    ad_creative_id: str,
    placement_id: str,
    action: str,
    timestamp: datetime | None = None,
    session_id: str | None = None,
    device_snapshot: dict[str, Any] | None = None,
    location_snapshot: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> AdInteraction:
    """
    Log an ad interaction event (append-only pattern, no updates/deletes).
    
    This function implements the append-only event logging pattern with schema versioning
    for backwards compatibility. All events are immutable once created.
    
    Args:
        session: Database session
        user_id: User identifier (UUID string)
        ad_type: Ad type (interstitial, reward, banner)
        ad_creative_id: Ad creative identifier
        placement_id: Placement identifier
        action: Action type (impression, click, skip, complete, dismiss, failure)
        timestamp: Event timestamp (defaults to now if not provided)
        session_id: Optional session ID to capture device/location snapshots from
        device_snapshot: Optional device snapshot (if not provided, will try to get from session)
        location_snapshot: Optional location snapshot (if not provided, will try to get from session)
        metadata: Action-specific metadata
        
    Returns:
        Created AdInteraction record
        
    Raises:
        ValueError: If validation fails
    """
    # Validate action and ad type
    validate_action_type(action)
    validate_ad_type(ad_type)
    
    # Validate and normalize metadata
    metadata = validate_metadata_structure(action, metadata)
    
    # Use provided timestamp or current time
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    # Capture device/location snapshots if not provided
    if device_snapshot is None or location_snapshot is None:
        captured_device, captured_location = capture_device_location_snapshots(session, session_id)
        if device_snapshot is None:
            device_snapshot = captured_device
        if location_snapshot is None:
            location_snapshot = captured_location
    
    # Handle out-of-order event arrival by using timestamps to reconstruct sequence
    # Events are stored with their original timestamp, allowing chronological reconstruction
    # even if they arrive out of order
    
    # Create interaction record (append-only, immutable)
    interaction = AdInteraction(
        user_id=user_id,
        session_id=session_id,
        ad_type=ad_type,
        ad_creative_id=ad_creative_id,
        placement_id=placement_id,
        action=action,
        timestamp=timestamp,
        device_snapshot=device_snapshot,
        location_snapshot=location_snapshot,
        metadata=metadata,
        schema_version=CURRENT_SCHEMA_VERSION,
    )
    
    session.add(interaction)
    session.commit()
    session.refresh(interaction)
    
    logger.info(
        f"Logged ad interaction: user_id={user_id}, ad_type={ad_type}, "
        f"ad_creative_id={ad_creative_id}, action={action}, timestamp={timestamp}"
    )
    
    return interaction


def get_interaction_by_id(session: Session, interaction_id: str) -> AdInteraction | None:
    """
    Get an ad interaction by ID.
    
    Args:
        session: Database session
        interaction_id: Interaction identifier (UUID string)
        
    Returns:
        AdInteraction record or None if not found
    """
    return session.get(AdInteraction, interaction_id)


def get_user_interactions(
    session: Session,
    user_id: str,
    limit: int = 100,
    offset: int = 0,
    ad_type: str | None = None,
    action: str | None = None,
) -> list[AdInteraction]:
    """
    Get ad interactions for a user with optional filtering.
    
    Args:
        session: Database session
        user_id: User identifier (UUID string)
        limit: Maximum number of results
        offset: Offset for pagination
        ad_type: Optional filter by ad type
        action: Optional filter by action type
        
    Returns:
        List of AdInteraction records
    """
    statement = select(AdInteraction).where(AdInteraction.user_id == user_id)
    
    if ad_type:
        statement = statement.where(AdInteraction.ad_type == ad_type)
    if action:
        statement = statement.where(AdInteraction.action == action)
    
    statement = statement.order_by(AdInteraction.timestamp.desc()).limit(limit).offset(offset)
    
    return list(session.exec(statement).all())

