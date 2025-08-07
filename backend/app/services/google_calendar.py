"""Google Calendar integration service."""
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings
from app.models.google_calendar import (
    GoogleCalendarAuth,
    GoogleCalendarCache,
    GoogleCalendarConfig,
    GoogleCalendarEvent,
    GoogleCalendarStatus,
)


class GoogleCalendarService:
    """Service for managing Google Calendar integration."""

    CACHE_FILE = Path("/app/config/google_calendar_cache.json")

    def __init__(self):
        """Initialize the Google Calendar service."""
        self.config = self._load_config()
        self.cache = self._load_cache()

    def _load_config(self) -> GoogleCalendarConfig:
        """Load Google Calendar configuration from environment."""
        return GoogleCalendarConfig(
            client_id=os.getenv("GOOGLE_CALENDAR_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET"),
            redirect_uri=os.getenv("GOOGLE_CALENDAR_REDIRECT_URI", "http://localhost:8000/api/v1/integrations/google-calendar/callback")
        )

    def _load_cache(self) -> GoogleCalendarCache:
        """Load cached Google Calendar data from file."""
        if self.CACHE_FILE.exists():
            try:
                with open(self.CACHE_FILE) as f:
                    data = json.load(f)
                    # Convert ISO strings back to datetime objects
                    if data.get("last_synced"):
                        data["last_synced"] = datetime.fromisoformat(data["last_synced"])
                    if data.get("auth") and data["auth"].get("expiry"):
                        data["auth"]["expiry"] = datetime.fromisoformat(data["auth"]["expiry"])
                    # Convert event dates
                    for event in data.get("events", []):
                        if event.get("start"):
                            event["start"] = datetime.fromisoformat(event["start"])
                        if event.get("end"):
                            event["end"] = datetime.fromisoformat(event["end"])
                        if event.get("created"):
                            event["created"] = datetime.fromisoformat(event["created"])
                        if event.get("updated"):
                            event["updated"] = datetime.fromisoformat(event["updated"])
                    return GoogleCalendarCache(**data)
            except Exception as e:
                print(f"Error loading Google Calendar cache: {e}")
        return GoogleCalendarCache()

    def _save_cache(self):
        """Save Google Calendar cache to file."""
        try:
            # Ensure config directory exists
            self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dict with ISO format dates
            cache_dict = self.cache.dict()
            with open(self.CACHE_FILE, "w") as f:
                json.dump(cache_dict, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving Google Calendar cache: {e}")

    def get_auth_url(self) -> str | None:
        """Generate OAuth authorization URL."""
        if not self.config.is_configured:
            return None

        # Use the same scopes for auth URL and callback
        expected_scopes = [
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid"
        ]

        flow = Flow.from_client_config(
            {
                "installed": {
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.config.redirect_uri]
                }
            },
            scopes=expected_scopes,
            redirect_uri=self.config.redirect_uri
        )

        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent"
        )

        return auth_url

    async def handle_oauth_callback(self, code: str) -> bool:
        """Handle OAuth callback and store credentials."""
        if not self.config.is_configured:
            return False

        try:
            # Create flow with all expected scopes including openid
            expected_scopes = [
                "https://www.googleapis.com/auth/calendar.readonly",
                "https://www.googleapis.com/auth/userinfo.email",
                "openid"
            ]
            
            flow = Flow.from_client_config(
                {
                    "installed": {
                        "client_id": self.config.client_id,
                        "client_secret": self.config.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.config.redirect_uri]
                    }
                },
                scopes=expected_scopes,
                redirect_uri=self.config.redirect_uri
            )

            # Exchange code for tokens
            flow.fetch_token(code=code)
            credentials = flow.credentials

            # Store auth data in cache
            self.cache.auth = GoogleCalendarAuth(
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_uri=credentials.token_uri,
                client_id=credentials.client_id,
                client_secret=credentials.client_secret,
                scopes=credentials.scopes,
                expiry=credentials.expiry
            )

            # Get user email
            service = build("oauth2", "v2", credentials=credentials)
            user_info = service.userinfo().get().execute()
            self.cache.user_email = user_info.get("email")

            # Save cache
            self._save_cache()

            # Initial sync
            await self.sync_events()

            return True

        except Exception as e:
            print(f"Error handling OAuth callback: {e}")
            return False

    def _get_credentials(self) -> Credentials | None:
        """Get valid Google credentials from cache."""
        if not self.cache.auth:
            return None

        try:
            credentials = Credentials(
                token=self.cache.auth.access_token,
                refresh_token=self.cache.auth.refresh_token,
                token_uri=self.cache.auth.token_uri,
                client_id=self.cache.auth.client_id,
                client_secret=self.cache.auth.client_secret,
                scopes=self.cache.auth.scopes,
                expiry=self.cache.auth.expiry
            )

            # Refresh if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                # Update cache with new token
                self.cache.auth.access_token = credentials.token
                self.cache.auth.expiry = credentials.expiry
                self._save_cache()

            return credentials

        except Exception as e:
            print(f"Error getting credentials: {e}")
            return None

    async def sync_events(self) -> bool:
        """Sync calendar events from the last 2 weeks."""
        credentials = self._get_credentials()
        if not credentials:
            return False

        try:
            # Build calendar service
            service = build("calendar", "v3", credentials=credentials)

            # Calculate time range (last 2 weeks)
            now = datetime.now(UTC)
            two_weeks_ago = now - timedelta(weeks=2)

            # Fetch events
            events_result = service.events().list(
                calendarId=self.cache.calendar_id,
                timeMin=two_weeks_ago.isoformat(),
                timeMax=now.isoformat(),
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            events = events_result.get("items", [])

            # Convert to our model
            calendar_events = []
            for event in events:
                # Parse start/end times
                start_data = event.get("start", {})
                end_data = event.get("end", {})

                if "dateTime" in start_data:
                    start = datetime.fromisoformat(start_data["dateTime"])
                    end = datetime.fromisoformat(end_data["dateTime"])
                    is_all_day = False
                else:
                    # All-day event
                    start = datetime.fromisoformat(start_data["date"] + "T00:00:00")
                    end = datetime.fromisoformat(end_data["date"] + "T00:00:00")
                    is_all_day = True

                # Parse created/updated times
                created = None
                if event.get("created"):
                    created = datetime.fromisoformat(event["created"].replace("Z", "+00:00"))

                updated = None
                if event.get("updated"):
                    updated = datetime.fromisoformat(event["updated"].replace("Z", "+00:00"))

                calendar_event = GoogleCalendarEvent(
                    id=event["id"],
                    summary=event.get("summary"),
                    description=event.get("description"),
                    location=event.get("location"),
                    start=start,
                    end=end,
                    created=created,
                    updated=updated,
                    status=event.get("status", "confirmed"),
                    attendees=event.get("attendees", []),
                    organizer=event.get("organizer"),
                    recurrence=event.get("recurrence"),
                    recurring_event_id=event.get("recurringEventId"),
                    is_all_day=is_all_day,
                    html_link=event.get("htmlLink")
                )
                calendar_events.append(calendar_event)

            # Update cache
            self.cache.events = calendar_events
            self.cache.last_synced = now
            self._save_cache()

            return True

        except HttpError as e:
            print(f"Google Calendar API error: {e}")
            return False
        except Exception as e:
            print(f"Error syncing events: {e}")
            return False

    def get_status(self) -> GoogleCalendarStatus:
        """Get current status of Google Calendar integration."""
        is_authenticated = bool(self.cache.auth and self._get_credentials())

        return GoogleCalendarStatus(
            is_configured=self.config.is_configured,
            is_authenticated=is_authenticated,
            user_email=self.cache.user_email if is_authenticated else None,
            event_count=len(self.cache.events),
            last_synced=self.cache.last_synced
        )

    def get_cached_events(self) -> list[GoogleCalendarEvent]:
        """Get cached calendar events."""
        return self.cache.events

    def disconnect(self):
        """Disconnect Google Calendar integration."""
        self.cache = GoogleCalendarCache()
        self._save_cache()


# Global instance
google_calendar_service = GoogleCalendarService()
