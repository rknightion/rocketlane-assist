"""Google Calendar integration models."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GoogleCalendarEvent(BaseModel):
    """Model for a Google Calendar event."""
    id: str
    summary: str | None = None
    description: str | None = None
    location: str | None = None
    start: datetime
    end: datetime
    created: datetime | None = None
    updated: datetime | None = None
    status: str = "confirmed"
    attendees: list[dict[str, Any]] = Field(default_factory=list)
    organizer: dict[str, Any] | None = None
    recurrence: list[str] | None = None
    recurring_event_id: str | None = None
    is_all_day: bool = False
    html_link: str | None = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class GoogleCalendarAuth(BaseModel):
    """Model for Google Calendar OAuth authentication data."""
    access_token: str
    refresh_token: str | None = None
    token_uri: str
    client_id: str
    client_secret: str
    scopes: list[str]
    expiry: datetime | None = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class GoogleCalendarCache(BaseModel):
    """Model for cached Google Calendar data."""
    auth: GoogleCalendarAuth | None = None
    events: list[GoogleCalendarEvent] = Field(default_factory=list)
    last_synced: datetime | None = None
    user_email: str | None = None
    calendar_id: str = "primary"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class GoogleCalendarConfig(BaseModel):
    """Configuration for Google Calendar integration."""
    client_id: str | None = None
    client_secret: str | None = None
    redirect_uri: str = "http://localhost:8000/api/v1/integrations/google-calendar/callback"
    scopes: list[str] = Field(default_factory=lambda: [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ])

    @property
    def is_configured(self) -> bool:
        """Check if Google Calendar OAuth is configured."""
        return bool(self.client_id and self.client_secret)


class GoogleCalendarStatus(BaseModel):
    """Status response for Google Calendar integration."""
    is_configured: bool
    is_authenticated: bool
    user_email: str | None = None
    event_count: int = 0
    last_synced: datetime | None = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
