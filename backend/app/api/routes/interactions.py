"""Ad interaction API routes."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.deps import SessionDep
from app.models import AdInteraction
from app.services.interactions import (
    get_interaction_by_id,
    get_user_interactions,
    log_ad_interaction,
)

router = APIRouter(prefix="/interactions", tags=["interactions"])


class InteractionMetadata(BaseModel):
    """Metadata schema for different action types."""
    
    # Click metadata
    time_since_impression: int | None = Field(default=None, description="Time since impression in seconds")
    click_position: dict[str, Any] | None = Field(default=None, description="Click position for banners")
    
    # Skip/dismiss metadata
    time_watched: int | None = Field(default=None, description="Time watched in seconds")
    skip_reason: str | None = Field(default=None, description="Reason for skipping")
    
    # Completion metadata
    total_watch_duration: int | None = Field(default=None, description="Total watch duration in seconds")
    reward_type: str | None = Field(default=None, description="Reward type")
    reward_amount: float | None = Field(default=None, description="Reward amount")
    verification_status: str | None = Field(default=None, description="Verification status")
    
    # Failure metadata
    error_code: str | None = Field(default=None, description="Error code")
    error_message: str | None = Field(default=None, description="Error message")


class InteractionCreateRequest(BaseModel):
    """Request model for creating an ad interaction."""
    
    user_id: str = Field(..., description="User identifier (openid or UUID)")
    ad_type: str = Field(..., description="Ad type (interstitial, reward, banner)")
    ad_creative_id: str = Field(..., description="Ad creative identifier")
    placement_id: str = Field(..., description="Placement identifier")
    action: str = Field(..., description="Action type (impression, click, skip, complete, dismiss, failure)")
    timestamp: datetime | None = Field(default=None, description="Event timestamp (defaults to now)")
    session_id: str | None = Field(default=None, description="Optional session ID")
    device_snapshot: dict[str, Any] | None = Field(default=None, description="Device snapshot (optional, will be captured from session if not provided)")
    location_snapshot: dict[str, Any] | None = Field(default=None, description="Location snapshot (optional, will be captured from session if not provided)")
    metadata: InteractionMetadata | None = Field(default=None, description="Action-specific metadata")


class InteractionResponse(BaseModel):
    """Response model for ad interaction."""
    
    interaction_id: uuid.UUID
    user_id: uuid.UUID
    session_id: uuid.UUID | None
    ad_type: str
    ad_creative_id: str
    placement_id: str
    action: str
    timestamp: datetime
    device_snapshot: dict[str, Any] | None
    location_snapshot: dict[str, Any] | None
    metadata: dict[str, Any] | None
    schema_version: int
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=InteractionResponse, status_code=201)
def create_interaction(
    interaction_data: InteractionCreateRequest,
    session: SessionDep,
) -> Any:
    """
    Log an ad interaction event.
    
    This endpoint implements append-only event logging. All events are immutable
    once created. Device and location snapshots are preserved at interaction time
    to maintain historical context.
    """
    try:
        metadata_dict = interaction_data.metadata.model_dump(exclude_none=True) if interaction_data.metadata else None
        
        interaction = log_ad_interaction(
            session=session,
            user_id=interaction_data.user_id,
            ad_type=interaction_data.ad_type,
            ad_creative_id=interaction_data.ad_creative_id,
            placement_id=interaction_data.placement_id,
            action=interaction_data.action,
            timestamp=interaction_data.timestamp,
            session_id=interaction_data.session_id,
            device_snapshot=interaction_data.device_snapshot,
            location_snapshot=interaction_data.location_snapshot,
            metadata=metadata_dict,
        )
        
        return InteractionResponse(
            interaction_id=interaction.interaction_id,
            user_id=interaction.user_id,
            session_id=interaction.session_id,
            ad_type=interaction.ad_type,
            ad_creative_id=interaction.ad_creative_id,
            placement_id=interaction.placement_id,
            action=interaction.action,
            timestamp=interaction.timestamp,
            device_snapshot=interaction.device_snapshot,
            location_snapshot=interaction.location_snapshot,
            metadata=interaction.metadata,
            schema_version=interaction.schema_version,
            created_at=interaction.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log interaction: {str(e)}")


@router.get("/{interaction_id}", response_model=InteractionResponse)
def get_interaction(
    interaction_id: uuid.UUID,
    session: SessionDep,
) -> Any:
    """
    Get an ad interaction by ID.
    
    Returns the interaction record with all preserved snapshots and metadata.
    """
    interaction = get_interaction_by_id(session, str(interaction_id))
    
    if not interaction:
        raise HTTPException(status_code=404, detail=f"Interaction {interaction_id} not found")
    
    return InteractionResponse(
        interaction_id=interaction.interaction_id,
        user_id=interaction.user_id,
        session_id=interaction.session_id,
        ad_type=interaction.ad_type,
        ad_creative_id=interaction.ad_creative_id,
        placement_id=interaction.placement_id,
        action=interaction.action,
        timestamp=interaction.timestamp,
        device_snapshot=interaction.device_snapshot,
        location_snapshot=interaction.location_snapshot,
        metadata=interaction.metadata,
        schema_version=interaction.schema_version,
        created_at=interaction.created_at,
    )


@router.get("", response_model=list[InteractionResponse])
def list_interactions(
    user_id: str | None = Query(default=None, description="Filter by user ID"),
    session_id: str | None = Query(default=None, description="Filter by session ID"),
    ad_type: str | None = Query(default=None, description="Filter by ad type"),
    action: str | None = Query(default=None, description="Filter by action type"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    session: SessionDep = None,
) -> Any:
    """
    List ad interactions with optional filtering.
    
    Supports filtering by user_id, session_id, ad_type, and action.
    Results are ordered by timestamp (most recent first).
    """
    try:
        interactions = get_user_interactions(
            session=session,
            user_id=user_id or "",
            limit=limit,
            offset=offset,
            ad_type=ad_type,
            action=action,
        )
        
        return [
            InteractionResponse(
                interaction_id=interaction.interaction_id,
                user_id=interaction.user_id,
                session_id=interaction.session_id,
                ad_type=interaction.ad_type,
                ad_creative_id=interaction.ad_creative_id,
                placement_id=interaction.placement_id,
                action=interaction.action,
                timestamp=interaction.timestamp,
                device_snapshot=interaction.device_snapshot,
                location_snapshot=interaction.location_snapshot,
                metadata=interaction.metadata,
                schema_version=interaction.schema_version,
                created_at=interaction.created_at,
            )
            for interaction in interactions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve interactions: {str(e)}")

