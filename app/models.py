"""Request and response models for the Honey-Pot API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# --- Incoming Message (from Mock Scammer API) ---


class MessageEvent(BaseModel):
    """Incoming message event from the Mock Scammer API."""
    model_config = ConfigDict(extra="allow")
    conversation_id: Optional[str] = Field(default="conversation_id",description="Unique identifier for the conversation")
    message: str = Field(..., description="The message content")
    sender: Optional[str] = Field(default="scammer", description="Sender identifier")
    timestamp: Optional[str] = Field(default=None, description="Message timestamp")


# --- Extracted Intelligence ---


class ExtractedIntelligence(BaseModel):
    """Structured intelligence extracted from the conversation."""

    bank_account_numbers: list[str] = Field(default_factory=list)
    upi_ids: list[str] = Field(default_factory=list)
    phishing_urls: list[str] = Field(default_factory=list)
    other_relevant_info: list[str] = Field(default_factory=list)


# --- Engagement Metrics ---


class EngagementMetrics(BaseModel):
    """Metrics about the engagement with the scammer."""

    conversation_turns: int = Field(default=0, description="Number of message exchanges")
    engagement_duration_seconds: Optional[float] = Field(default=None)
    scam_detected_at_turn: Optional[int] = Field(default=None)
    agent_activated: bool = Field(default=False)


# --- API Response ---


class HoneyPotResponse(BaseModel):
    """Structured API response for the Honey-Pot system."""

    scam_detected: bool = Field(..., description="Whether scam intent was detected")
    response_message: str = Field(..., description="The message to send back to the scammer")
    engagement_metrics: EngagementMetrics = Field(default_factory=EngagementMetrics)
    extracted_intelligence: ExtractedIntelligence = Field(default_factory=ExtractedIntelligence)
    conversation_id: Optional[str] = Field(..., description="Conversation identifier")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")