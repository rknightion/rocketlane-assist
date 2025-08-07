"""API endpoints for integrations."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.models.google_calendar import GoogleCalendarEvent, GoogleCalendarStatus
from app.services.google_calendar import google_calendar_service

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/google-calendar/status", response_model=GoogleCalendarStatus)
async def get_google_calendar_status():
    """Get the status of Google Calendar integration."""
    return google_calendar_service.get_status()


@router.get("/google-calendar/auth")
async def start_google_calendar_auth():
    """Start Google Calendar OAuth flow."""
    auth_url = google_calendar_service.get_auth_url()
    if not auth_url:
        raise HTTPException(
            status_code=400,
            detail="Google Calendar OAuth is not configured. Please set GOOGLE_CALENDAR_CLIENT_ID and GOOGLE_CALENDAR_CLIENT_SECRET environment variables."
        )
    return {"auth_url": auth_url}


@router.get("/google-calendar/callback")
async def google_calendar_callback(code: str = Query(...)):
    """Handle Google Calendar OAuth callback."""
    success = await google_calendar_service.handle_oauth_callback(code)
    if success:
        # Redirect to frontend settings page with success message
        return RedirectResponse(url="http://localhost:3000/settings?gcal_connected=true")
    else:
        # Redirect with error
        return RedirectResponse(url="http://localhost:3000/settings?gcal_error=true")


@router.post("/google-calendar/sync")
async def sync_google_calendar():
    """Manually trigger Google Calendar sync."""
    success = await google_calendar_service.sync_events()
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to sync Google Calendar events. Please check your authentication."
        )

    status = google_calendar_service.get_status()
    return {
        "success": True,
        "event_count": status.event_count,
        "last_synced": status.last_synced
    }


@router.get("/google-calendar/events", response_model=list[GoogleCalendarEvent])
async def get_google_calendar_events():
    """Get cached Google Calendar events."""
    status = google_calendar_service.get_status()
    if not status.is_authenticated:
        raise HTTPException(
            status_code=401,
            detail="Google Calendar is not authenticated. Please connect your account first."
        )

    return google_calendar_service.get_cached_events()


@router.post("/google-calendar/disconnect")
async def disconnect_google_calendar():
    """Disconnect Google Calendar integration."""
    google_calendar_service.disconnect()
    return {"success": True, "message": "Google Calendar disconnected successfully"}
