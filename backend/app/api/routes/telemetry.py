"""Telemetry collection API routes."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.deps import SessionDep
from app.models import UserSession
from app.services.telemetry import create_session, update_session_end_time

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


class DeviceSnapshot(BaseModel):
    """Device snapshot schema."""
    
    os_family: str = Field(..., description="OS family (e.g., iOS, Android, Web)")
    device_class: str = Field(..., description="Device class (mobile, tablet, desktop)")
    os_version: str | None = Field(default=None, description="OS version")
    screen_resolution: str | None = Field(default=None, description="Screen resolution (e.g., 1920x1080)")
    screen_density: float | None = Field(default=None, description="Screen density (DPI/PPI)")
    viewport_width: int | None = Field(default=None, description="Viewport width in pixels")
    viewport_height: int | None = Field(default=None, description="Viewport height in pixels")


class LocationSnapshot(BaseModel):
    """Location snapshot schema."""
    
    country: str = Field(..., description="Country code")
    city: str | None = Field(default=None, description="City name")
    latitude: float | None = Field(default=None, description="Latitude (opt-in precise location)")
    longitude: float | None = Field(default=None, description="Longitude (opt-in precise location)")
    location_source: str | None = Field(default="IP", description="Location source (IP or precise)")


class SessionCreateRequest(BaseModel):
    """Request model for creating a session."""
    
    user_id: str = Field(..., description="User identifier (openid or UUID)")
    ip_address: str = Field(..., description="User's IP address")
    device_snapshot: DeviceSnapshot | None = Field(default=None, description="Device information snapshot")
    location_snapshot: LocationSnapshot | None = Field(default=None, description="Location information snapshot (optional, will be enriched from IP)")
    opt_out_flags: dict[str, Any] | None = Field(default=None, description="User opt-out preferences")


class SessionUpdateRequest(BaseModel):
    """Request model for updating a session."""
    
    end_timestamp: datetime | None = Field(default=None, description="Session end timestamp (defaults to now if not provided)")


class SessionResponse(BaseModel):
    """Response model for session."""
    
    id: uuid.UUID
    user_id: uuid.UUID
    start_timestamp: datetime
    end_timestamp: datetime | None
    duration: int | None
    ip_address: str
    device_snapshot: dict[str, Any] | None
    location_snapshot: dict[str, Any] | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/session", response_model=SessionResponse)
def create_telemetry_session(
    session_data: SessionCreateRequest,
    session: SessionDep,
    x_forwarded_for: str | None = None,
) -> Any:
    """
    Create a new telemetry session.
    
    Captures device and location information, creates user session,
    and preserves snapshots in device/location history.
    """
    # Use X-Forwarded-For header if available (for proxied requests)
    ip_address = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else session_data.ip_address
    
    try:
        device_snapshot_dict = session_data.device_snapshot.model_dump() if session_data.device_snapshot else None
        location_snapshot_dict = session_data.location_snapshot.model_dump() if session_data.location_snapshot else None
        
        user_session = create_session(
            session=session,
            user_id=session_data.user_id,
            ip_address=ip_address,
            device_snapshot=device_snapshot_dict,
            location_snapshot=location_snapshot_dict,
            opt_out_flags=session_data.opt_out_flags,
        )
        
        return SessionResponse(
            id=user_session.id,
            user_id=user_session.user_id,
            start_timestamp=user_session.start_timestamp,
            end_timestamp=user_session.end_timestamp,
            duration=user_session.duration,
            ip_address=user_session.ip_address,
            device_snapshot=user_session.device_snapshot,
            location_snapshot=user_session.location_snapshot,
            created_at=user_session.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.patch("/session/{session_id}", response_model=SessionResponse)
def update_telemetry_session(
    session_id: uuid.UUID,
    session_data: SessionUpdateRequest,
    session: SessionDep,
) -> Any:
    """
    Update session end time.
    
    Updates the session end timestamp and calculates duration.
    """
    try:
        user_session = update_session_end_time(
            session=session,
            session_id=str(session_id),
            end_timestamp=session_data.end_timestamp,
        )
        
        return SessionResponse(
            id=user_session.id,
            user_id=user_session.user_id,
            start_timestamp=user_session.start_timestamp,
            end_timestamp=user_session.end_timestamp,
            duration=user_session.duration,
            ip_address=user_session.ip_address,
            device_snapshot=user_session.device_snapshot,
            location_snapshot=user_session.location_snapshot,
            created_at=user_session.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")

